package kr.pureun.travel;

import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.Locale;
import java.util.Set;

/** 목소리: 휴대폰 TTS를 웹의 speechSynthesis처럼 쓰게 해 준다. */
class TtsEngine {
    private final MainActivity act;
    private TextToSpeech tts;
    private volatile boolean ready;
    private volatile String voicesJson = "[]";

    TtsEngine(MainActivity a) {
        act = a;
        tts = new TextToSpeech(a.getApplicationContext(), new TextToSpeech.OnInitListener() {
            @Override public void onInit(int status) {
                ready = status == TextToSpeech.SUCCESS;
                if (!ready) return;
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override public void onStart(String id) { send(id, "start", 0); }
                    @Override public void onDone(String id) { send(id, "end", 0); }
                    @Override public void onError(String id) { send(id, "error", 0); }
                    @Override public void onError(String id, int code) { send(id, "error", 0); }
                    @Override public void onStop(String id, boolean interrupted) { /* cancel: 알리지 않음 */ }
                    @Override public void onRangeStart(String id, int start, int end, int frame) { send(id, "boundary", start); }
                });
                loadVoices();
                act.emit("onVoices", "0");
            }
        });
    }

    private void send(String id, String type, int charIndex) {
        act.emit("onTts", "{\"id\":" + id + ",\"type\":\"" + type + "\",\"charIndex\":" + charIndex + "}");
    }

    private void loadVoices() {
        try {
            JSONArray arr = new JSONArray();
            Set<Voice> vs = tts.getVoices();
            if (vs != null) for (Voice v : vs) {
                if (v == null || v.getLocale() == null) continue;
                Set<String> f = v.getFeatures();
                if (f != null && f.contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED)) continue;
                JSONObject o = new JSONObject();
                o.put("name", v.getName());
                o.put("lang", v.getLocale().toLanguageTag());
                o.put("localService", !v.isNetworkConnectionRequired());
                o.put("q", v.getQuality());                     // 품질: 300 보통 · 400 높음 · 500 아주 높음
                arr.put(o);
            }
            voicesJson = arr.toString();
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "voices", t);
        }
    }

    String voices() { return voicesJson; }

    /** 휴대폰이 기본으로 쓰는 목소리 엔진 (음성 데이터 설치 화면을 열 때 씀) */
    String engine() { try { return tts == null ? null : tts.getDefaultEngine(); } catch (Throwable t) { return null; } }

    void speak(final int id, final String text, final String lang, final float rate, final String voice, final float volume) {
        if (!ready) { send(String.valueOf(id), "error", 0); return; }
        try {
            boolean set = false;
            if (voice != null && !voice.isEmpty()) {
                Set<Voice> vs = tts.getVoices();
                if (vs != null) for (Voice v : vs) {
                    if (voice.equals(v.getName())) { tts.setVoice(v); set = true; break; }
                }
            }
            if (!set) {
                Locale loc = Locale.forLanguageTag(lang == null || lang.isEmpty() ? "ko-KR" : lang);
                int r = tts.setLanguage(loc);
                if (r == TextToSpeech.LANG_MISSING_DATA || r == TextToSpeech.LANG_NOT_SUPPORTED)
                    tts.setLanguage(new Locale(loc.getLanguage()));
            }
            tts.setSpeechRate(rate > 0 ? rate : 1f);
            Bundle b = new Bundle();
            if (volume > 0 && volume < 1f) b.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, volume);
            int res = tts.speak(text, TextToSpeech.QUEUE_ADD, b, String.valueOf(id));
            if (res != TextToSpeech.SUCCESS) send(String.valueOf(id), "error", 0);
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "tts", t);
            send(String.valueOf(id), "error", 0);
        }
    }

    void cancel() {
        try { if (tts != null) tts.stop(); } catch (Exception ignored) { }
    }

    void shutdown() {
        try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception ignored) { }
        tts = null; ready = false;
    }
}
