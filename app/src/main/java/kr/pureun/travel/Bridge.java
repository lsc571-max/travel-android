package kr.pureun.travel;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** 화면(JS)에서 부르는 창구. window.AndroidBridge.xxx() */
class Bridge {
    private final MainActivity act;
    private final ExecutorService llmPool = Executors.newSingleThreadExecutor();
    private OutputStream saveOut;
    private Uri saveUri;
    private String saveName = "";

    Bridge(MainActivity a) { act = a; }

    @JavascriptInterface
    public String info() {
        try {
            JSONObject o = new JSONObject();
            o.put("version", act.getPackageManager().getPackageInfo(act.getPackageName(), 0).versionName);
            o.put("sdk", Build.VERSION.SDK_INT);
            o.put("device", Build.MANUFACTURER + " " + Build.MODEL);
            o.put("stt", act.stt.available());
            o.put("sttOffline", act.stt.offlineAvailable());
            o.put("llmEngine", act.llm.available());
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    // ── 음성 인식 ──
    @JavascriptInterface
    public void sttStart(final int sid, final String lang, final boolean continuous, final boolean preferOffline) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.start(sid, lang, continuous, preferOffline); } });
    }

    @JavascriptInterface
    public void sttStop(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.stop(sid); } });
    }

    @JavascriptInterface
    public void sttAbort(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.abort(sid); } });
    }

    // ── 끊기지 않는 마이크 (폰 안 음성 인식) ──
    @JavascriptInterface
    public String lsttInfo() { return act.lstt.infoJson(); }

    @JavascriptInterface
    public void lsttStart(final int sid, final String lang, final boolean continuous) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.start(sid, lang, continuous); } });
    }

    /** noDecode = true: 받아 적지 않고 말소리 구간(저장된 소리의 자리)만 알려 줌 (Gemini가 소리를 직접 들을 때) */
    @JavascriptInterface
    public void lsttStart2(final int sid, final String lang, final boolean continuous, final boolean noDecode) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.start(sid, lang, continuous, noDecode); } });
    }

    /** 저장해 둔 소리(name 파일의 a~b 표본)를 폰 안 AI로 받아 적음 → onSttFile */
    @JavascriptInterface
    public void lsttFile(final int reqId, final String name, final String a, final String b, final String lang) {
        long x = 0, y = 0;
        try { x = Long.parseLong(a); y = Long.parseLong(b); } catch (Exception ignored) { }
        act.lstt.transcribeFile(reqId, name, x, y, lang);
    }

    /** 화면이 가진 소리(녹음)를 임시 파일로 넘김 → lsttFile로 받아 적음 */
    @JavascriptInterface
    public boolean recWrite(String name, String b64, boolean first) { return LocalStt.recWrite(act, name, b64, first); }

    /** 저장한 기록이 쓰는 소리 파일을 5일 뒤에도 지우지 않게 (on) / 다시 지워도 되게 (off) */
    @JavascriptInterface
    public void recKeep(String name, boolean on) { LocalStt.recKeep(act, name, on); }

    /** 마이크 고르기: "auto" · "phone" · "ear" */
    @JavascriptInterface
    public void setMic(String pref) { act.lstt.setMic(pref); }

    /** how: "stop" 마지막까지 받아 적고 끝 · "abort" 버리고 끝 · "detach" 마이크는 두고 세션만 끝 */
    @JavascriptInterface
    public void lsttEnd(final int sid, final String how) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                if ("stop".equals(how)) act.lstt.stop(sid);
                else if ("detach".equals(how)) act.lstt.detach(sid);
                else act.lstt.abort(sid);
            }
        });
    }

    /** AI 통역사: 마이크 소리를 그대로 화면으로 흘려보내기 */
    @JavascriptInterface
    public void pcmStart(final boolean echoCancel) {
        act.ui.post(new Runnable() { @Override public void run() { act.lstt.pcmStart(echoCancel); } });
    }

    @JavascriptInterface
    public void pcmStop() { act.lstt.pcmStop(); }

    /** 이어폰(유선·블루투스)이 연결돼 있는지 */
    @JavascriptInterface
    public boolean headset() {
        try {
            android.media.AudioManager am = (android.media.AudioManager) act.getSystemService(Context.AUDIO_SERVICE);
            for (android.media.AudioDeviceInfo d : am.getDevices(android.media.AudioManager.GET_DEVICES_OUTPUTS)) {
                int t = d.getType();
                if (t == android.media.AudioDeviceInfo.TYPE_WIRED_HEADSET || t == android.media.AudioDeviceInfo.TYPE_WIRED_HEADPHONES
                        || t == android.media.AudioDeviceInfo.TYPE_BLUETOOTH_A2DP || t == android.media.AudioDeviceInfo.TYPE_BLUETOOTH_SCO
                        || t == android.media.AudioDeviceInfo.TYPE_USB_HEADSET || t == 26 /* BLE 헤드셋 */)
                    return true;
            }
        } catch (Throwable ignored) { }
        return false;
    }

    /** 화면이 꺼져도 계속 듣게 할지 (듣기 모드 + 폰 안 음성 인식일 때 화면 쪽에서 켬) */
    @JavascriptInterface
    public void setBackground(boolean on) { act.bgKeep = on; }

    /** 통역 소리를 읽는 중인지 (읽는 동안에는 화면이 꺼져도 멈추지 않게) */
    @JavascriptInterface
    public void setPlaying(final boolean on) {
        act.playKeep = on;
        act.runOnUiThread(new Runnable() { @Override public void run() { if (on) PlayService.start(act); else PlayService.stop(act); } });
    }

    // ── 목소리 ──
    @JavascriptInterface
    public String ttsVoices() { return act.tts.voices(); }

    @JavascriptInterface
    public void ttsSpeak(final int id, final String text, final String lang, final float rate, final String voice, final float volume) {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.speak(id, text, lang, rate, voice, volume); } });
    }

    @JavascriptInterface
    public void ttsCancel() {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.cancel(); } });
    }

    // ── 폰 안 번역 AI ──
    @JavascriptInterface
    public String llmState() { return act.llm.stateJson(); }

    @JavascriptInterface
    public void llmEnsure() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.ensure(); } });
    }

    @JavascriptInterface
    public void llmStop() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.stop(); } });
    }

    @JavascriptInterface
    public void llmChat(final int reqId, final String bodyJson) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                JSONObject o = new JSONObject();
                try {
                    o.put("id", reqId);
                    try {
                        o.put("text", act.llm.chat(bodyJson));
                        o.put("ok", true);
                    } catch (Throwable t) {
                        o.put("ok", false);
                        o.put("error", t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage());
                    }
                } catch (Exception ignored) { }
                act.emit("onLlm", o.toString());
            }
        });
    }

    @JavascriptInterface
    public String models() { return act.models.listJson(); }

    @JavascriptInterface
    public void modelDownload(String id) { act.models.download(id); }

    @JavascriptInterface
    public void modelCancel(String id) { act.models.cancel(id); }

    @JavascriptInterface
    public void modelDelete(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                ModelStore.Model m = act.models.find(id);
                if (m == null) return;
                if ("mt".equals(m.kind)) {
                    if (id.equals(act.models.selectedId("mt"))) act.llm.stop();
                    act.models.delete(id);
                    act.emit("onLlmState", act.llm.stateJson());
                } else {
                    act.models.delete(id);
                    act.ui.post(new Runnable() { @Override public void run() { act.lstt.modelChanged(); } });
                }
            }
        });
    }

    @JavascriptInterface
    public void modelSelect(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                ModelStore.Model m = act.models.find(id);
                if (m == null) return;
                act.models.select(id);
                if ("mt".equals(m.kind)) act.llm.ensure();
                else act.ui.post(new Runnable() { @Override public void run() { act.lstt.modelChanged(); } });
            }
        });
    }

    @JavascriptInterface
    public String modelAdd(String name, String url) { return act.models.addCustom(name, url); }

    // ── 공유·복사·붙여넣기 ──
    @JavascriptInterface
    public void share(final String title, final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    Intent i = new Intent(Intent.ACTION_SEND);
                    i.setType("text/plain");
                    i.putExtra(Intent.EXTRA_SUBJECT, title);
                    i.putExtra(Intent.EXTRA_TEXT, text);
                    act.startActivity(Intent.createChooser(i, title));
                } catch (Exception e) { Log.w(MainActivity.TAG, "share", e); }
            }
        });
    }

    @JavascriptInterface
    public void copy(final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
                    cm.setPrimaryClip(ClipData.newPlainText("text", text));
                } catch (Exception ignored) { }
            }
        });
    }

    @JavascriptInterface
    public String paste() {
        try {
            ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData d = cm.getPrimaryClip();
            if (d == null || d.getItemCount() == 0) return "";
            CharSequence t = d.getItemAt(0).coerceToText(act);
            return t == null ? "" : t.toString();
        } catch (Throwable t) { return ""; }
    }

    // ── 파일 저장 (내려받기 폴더) : saveBegin → saveChunk… → saveEnd ──
    @JavascriptInterface
    public synchronized boolean saveBegin(String name, String mime) {
        try {
            saveAbort();
            saveName = name;
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, name);
                v.put(MediaStore.Downloads.MIME_TYPE, mime == null || mime.isEmpty() ? "application/octet-stream" : mime);
                v.put(MediaStore.Downloads.IS_PENDING, 1);
                saveUri = act.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                saveOut = act.getContentResolver().openOutputStream(saveUri);
            } else {
                File d = act.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                saveOut = new FileOutputStream(new File(d, name));
            }
            return saveOut != null;
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "save", t);
            saveAbort();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized boolean saveChunk(String b64) {
        try {
            if (saveOut == null) return false;
            saveOut.write(Base64.decode(b64, Base64.DEFAULT));
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    @JavascriptInterface
    public synchronized boolean saveEnd() {
        try {
            if (saveOut == null) return false;
            saveOut.close();
            saveOut = null;
            if (saveUri != null && Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.IS_PENDING, 0);
                act.getContentResolver().update(saveUri, v, null, null);
            }
            saveUri = null;
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    private void saveAbort() {
        try { if (saveOut != null) saveOut.close(); } catch (Exception ignored) { }
        saveOut = null;
        if (saveUri != null) try { act.getContentResolver().delete(saveUri, null, null); } catch (Exception ignored) { }
        saveUri = null;
    }

    @JavascriptInterface
    public void keepAwake(boolean on) { act.keepAwake("js", on); }

    @JavascriptInterface
    public void openUrl(final String url) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try { act.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception ignored) { }
            }
        });
    }
}
