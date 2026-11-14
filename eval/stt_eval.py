# 음성 인식 모델 비교 (한국어 낭독 녹음 25개): 글자 오류율(CER, 낮을수록 좋음)과 속도
import io, re, time, sys
import numpy as np, soundfile as sf, sherpa_onnx
from datasets import load_dataset, Audio
from huggingface_hub import hf_hub_download
ds = load_dataset('Bingsu/zeroth-korean', split='test', streaming=True).cast_column('audio', Audio(decode=False))
S = []
for x in ds:
    a, sr = sf.read(io.BytesIO(x['audio']['bytes']), dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    S.append((a, sr, x['text']))
    if len(S) >= 25: break
dur = sum(len(a) / sr for a, sr, _ in S)
print(f'EVAL|STT|녹음 {len(S)}개 · {dur:.0f}초', flush=True)
nz = lambda t: re.sub(r'[\s.,!?~"\'·…]', '', t)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1]
for name in sys.argv[1:]:
    try:
        repo = 'csukuangfj/sherpa-onnx-whisper-' + name
        f = lambda s: hf_hub_download(repo, f'{name}-{s}')
        rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f('encoder.int8.onnx'), decoder=f('decoder.int8.onnx'), tokens=f('tokens.txt'), language='ko', task='transcribe', num_threads=4)
        err = n = 0; t0 = time.time(); ex = []
        for a, sr, ref in S:
            st = rec.create_stream(); st.accept_waveform(sr, a); rec.decode_stream(st)
            hyp = st.result.text.strip(); e = ed(nz(ref), nz(hyp)); err += e; n += len(nz(ref))
            if e and len(ex) < 3: ex.append(f'정답: {ref} / 인식: {hyp}')
        el = time.time() - t0
        print(f'EVAL|STT|{name}|글자 오류율 {100*err/n:.1f}% · {dur:.0f}초 분량을 {el:.0f}초에 처리 (소리 1초당 {el/dur:.2f}초, 4코어 서버)', flush=True)
        for x in ex: print(f'EVAL|STT|{name}|예|{x}')
    except Exception as e: print(f'EVAL|STT|{name}|ERR {e}', flush=True)
