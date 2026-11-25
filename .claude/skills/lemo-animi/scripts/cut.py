# cut.py -- cut-out (BiRefNet-general ONNX, local CPU); writes one matte per image <name>-mask.png (8-bit grey, white =
# subject, same size as the source)
#
# Usage:
#   python cut.py <out dir> <images...> [--threads N] [--workers W] [--skip-existing]
#     --threads N      onnxruntime threads per process (default = CPU cores / workers)
#     --workers W      parallel processes (default 1; each loads its own model, ~2 GB extra memory; keep it low on small machines)
#     --skip-existing  skip images whose matte exists (saves time on re-runs)
#   e.g. python cut.py work/masks work/cells/run_*.png
# Or import it:
#   import cut; s = cut.session(); m = cut.predict(s, rgb_uint8)   # -> float32 0–1 matte
#
# Model lookup order (first one that exists wins):
#   1. $LEMO_ANIMI_MODELS/birefnet-general.onnx
#   2. ${LEMO_ANIMI_HOME:-~/lemo-animi-env}/models/birefnet-general.onnx   (setup.sh's default download location)
#   3. ~/.rembg/models/birefnet-general/birefnet-general.onnx             (rembg's cache)
# None found: run sh setup.sh first (downloads the ~0.97 GB model).
# Tip: for a sheet on white, slice into cells first, then cut out -- cleanest; ~3–5 s per cell on CPU (20 s+ when several
# films cut out at once).
import sys, os, argparse
import numpy as np, cv2

MODEL_NAME = 'birefnet-general.onnx'
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def model_candidates():
    ex = os.path.expanduser; c = []
    if os.environ.get('LEMO_ANIMI_MODELS'):
        c.append(os.path.join(ex(os.environ['LEMO_ANIMI_MODELS']), MODEL_NAME))
    c.append(os.path.join(ex(os.environ.get('LEMO_ANIMI_HOME', '~/lemo-animi-env')), 'models', MODEL_NAME))
    c.append(ex('~/.rembg/models/birefnet-general/birefnet-general.onnx'))
    return c


def find_model():
    """-> model path; raises FileNotFoundError with a hint when not found"""
    for p in model_candidates():
        if os.path.isfile(p): return p
    raise FileNotFoundError('cut-out model birefnet-general.onnx not found; looked in:\n  ' + '\n  '.join(model_candidates())
                            + '\nRun sh setup.sh first (downloads ~0.97 GB), or set LEMO_ANIMI_MODELS to the folder holding the model.')


def session(threads=None, model=None):
    import onnxruntime as ort
    so = ort.SessionOptions()
    if threads: so.intra_op_num_threads = int(threads); so.inter_op_num_threads = 1
    return ort.InferenceSession(model or find_model(), so, providers=['CPUExecutionProvider'])


def predict(sess, rgb):
    """rgb: H×W×3 uint8 (RGB) -> H×W float32 matte 0–1"""
    h, w = rgb.shape[:2]
    x = cv2.resize(rgb, (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    inp = sess.get_inputs()[0]
    y = sess.run(None, {inp.name: x})[0]
    y = y[0, 0] if y.ndim == 4 else y[0]
    if y.min() < 0 or y.max() > 1: y = 1 / (1 + np.exp(-y))
    return np.clip(cv2.resize(y.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR), 0, 1)


def out_path(outdir, p):
    return os.path.join(outdir, os.path.splitext(os.path.basename(p))[0] + '-mask.png')


_S = None
def _init(threads, model):
    global _S
    cv2.setNumThreads(1)          # cv2's own thread pool fights onnxruntime for cores
    _S = session(threads, model)


def _job(args):
    p, outdir = args
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    if im is None: return p, 'unreadable, skipped'
    m = predict(_S, np.ascontiguousarray(im[:, :, ::-1]))
    cv2.imwrite(out_path(outdir, p), (m * 255 + 0.5).astype(np.uint8))
    return p, 'ok'


def main(argv=None):
    ap = argparse.ArgumentParser(description='BiRefNet cut-out: writes <name>-mask.png per image')
    ap.add_argument('outdir'); ap.add_argument('images', nargs='+')
    ap.add_argument('--threads', type=int, default=0); ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--skip-existing', action='store_true')
    a = ap.parse_args(argv)
    try: model = find_model()
    except FileNotFoundError as e: sys.exit(str(e))
    os.makedirs(a.outdir, exist_ok=True)
    todo = [p for p in a.images if not (a.skip_existing and os.path.exists(out_path(a.outdir, p)))]
    if not todo: print('all exist, skipped', file=sys.stderr); return
    workers = max(1, min(a.workers, len(todo)))
    threads = a.threads or max(1, (os.cpu_count() or 4) // workers)
    jobs = [(p, a.outdir) for p in todo]
    if workers == 1:
        _init(threads, model)
        for j in jobs: print(*_job(j), file=sys.stderr)
    else:
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(workers, _init, (threads, model)) as pool:
            for r in pool.imap_unordered(_job, jobs): print(*r, file=sys.stderr)


if __name__ == '__main__':
    main()
