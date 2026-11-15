package kr.pureun.travel;

import android.content.SharedPreferences;
import android.os.StatFs;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** 폰 안 AI 모델 파일 목록·내려받기·지우기·고르기. kind: "mt" 번역(GGUF) · "stt" 음성 인식 */
class ModelStore {
    static class Model {
        String id, kind, type, name, note, langs; String[][] files; long approx; boolean custom;
        Model(String id, String kind, String type, String name, String note, String langs, String[][] files, long approx, boolean custom) {
            this.id = id; this.kind = kind; this.type = type; this.name = name; this.note = note; this.langs = langs;
            this.files = files; this.approx = approx; this.custom = custom;
        }
    }

    static class Job { volatile boolean cancel; volatile long done, total; }

    private final MainActivity act;
    private final SharedPreferences prefs;
    private final File dir;
    private final Map<String, Job> jobs = new HashMap<>();

    ModelStore(MainActivity a) {
        act = a;
        prefs = a.getSharedPreferences("models", 0);
        // 앱 전용 내부 저장소 (엔진이 가장 빠르고 확실하게 읽을 수 있는 곳)
        File d = new File(a.getFilesDir(), "models");
        d.mkdirs();
        dir = d;
        // 내 폰 전용으로 정리하면서 목록에서 뺀 모델(Hy-MT2 · Whisper small · SenseVoice)의 파일은 지워 저장 공간을 돌려줌
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    for (String n : new String[]{"Hy-MT2-1.8B-Q4_K_M.gguf", "Hy-MT2-1.8B-Q6_K.gguf"}) { new File(dir, n).delete(); new File(dir, n + ".part").delete(); }
                    for (String n : new String[]{"whisper-small", "sensevoice"}) {
                        File sub = new File(dir, n);
                        File[] fs = sub.listFiles();
                        if (fs != null) for (File f : fs) f.delete();
                        sub.delete();
                    }
                } catch (Throwable ignored) { }
            }
        }, "model-clean").start();
    }

    List<Model> catalog() {
        List<Model> l = new ArrayList<>();
        // 정리+번역을 한 번에 하는 범용 AI (type "chat"): 받아쓴 글을 다듬고 번역까지. 시험에서 가장 정확했던 구성
        String g4 = "https://huggingface.co/google/gemma-4-E4B-it-qat-q4_0-gguf/resolve/main/";
        l.add(new Model("gemma4-e4b", "mt", "chat", "Gemma 4 (4B) · 정확", "권장(S24 울트라) · 한글 정리+번역 · 가장 정확 · 느림 · 램 12GB 이상", "",
                new String[][]{{g4 + "gemma-4-E4B_q4_0-it.gguf", "gemma-4-E4B_q4_0-it.gguf"}}, 5150000000L, false));
        String g2 = "https://huggingface.co/google/gemma-4-E2B-it-qat-q4_0-gguf/resolve/main/";
        l.add(new Model("gemma4-e2b", "mt", "chat", "Gemma 4 (2B) · 빠름", "한글 정리+번역 · 2배쯤 빠름 · 가끔 틀림", "",
                new String[][]{{g2 + "gemma-4-E2B_q4_0-it.gguf", "gemma-4-E2B_q4_0-it.gguf"}}, 3350000000L, false));
        // 음성 인식: Whisper turbo (모든 언어)
        String wt = "https://huggingface.co/csukuangfj/sherpa-onnx-whisper-turbo/resolve/main/";
        l.add(new Model("whisper-turbo", "stt", "whisper", "Whisper turbo · 정확", "권장 · 모든 언어 · 시험에서 small보다 훨씬 정확", "",
                new String[][]{{wt + "turbo-encoder.int8.onnx", "turbo-encoder.int8.onnx"}, {wt + "turbo-decoder.int8.onnx", "turbo-decoder.int8.onnx"}, {wt + "turbo-tokens.txt", "turbo-tokens.txt"}},
                1040000000L, false));
        try {
            JSONArray arr = new JSONArray(prefs.getString("custom", "[]"));
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                l.add(new Model(o.getString("id"), "mt", "gguf", o.getString("name"), "직접 넣은 모델", "",
                        new String[][]{{o.getString("url"), o.getString("file")}}, 0, true));
            }
        } catch (Exception ignored) { }
        return l;
    }

    Model find(String id) {
        for (Model m : catalog()) if (m.id.equals(id)) return m;
        return null;
    }

    /** 번역 모델은 models/ 바로 아래, 음성 인식 모델은 models/<id>/ 아래 */
    File fileOf(Model m, int i) {
        if ("mt".equals(m.kind)) return new File(dir, m.files[i][1]);
        File d = new File(dir, m.id);
        d.mkdirs();
        return new File(d, m.files[i][1]);
    }

    private File partOf(Model m, int i) { File f = fileOf(m, i); return new File(f.getParentFile(), f.getName() + ".part"); }

    boolean ready(Model m) {
        for (int i = 0; i < m.files.length; i++) if (!fileOf(m, i).exists()) return false;
        return true;
    }

    private long have(Model m) {
        long n = 0;
        for (int i = 0; i < m.files.length; i++) {
            File f = fileOf(m, i), p = partOf(m, i);
            n += f.exists() ? f.length() : p.exists() ? p.length() : 0;
        }
        return n;
    }

    String selectedId(String kind) {
        String sel = prefs.getString("mt".equals(kind) ? "selected" : "selected_" + kind, "");
        Model m = find(sel);
        if (m != null && m.kind.equals(kind) && ready(m)) return sel;
        for (Model x : catalog()) if (x.kind.equals(kind) && ready(x)) return x.id; // 고른 것이 없으면 받아 둔 첫 모델
        return "";
    }

    Model selected(String kind) { return find(selectedId(kind)); }

    File selectedFile() {
        Model m = selected("mt");
        return m == null ? null : fileOf(m, 0);
    }

    void select(String id) {
        Model m = find(id);
        if (m == null) return;
        prefs.edit().putString("mt".equals(m.kind) ? "selected" : "selected_" + m.kind, id).apply();
    }

    String listJson() {
        JSONArray arr = new JSONArray();
        try {
            for (Model m : catalog()) {
                JSONObject o = new JSONObject();
                Job j;
                synchronized (jobs) { j = jobs.get(m.id); }
                long have = have(m);
                o.put("id", m.id); o.put("kind", m.kind); o.put("type", m.type); o.put("name", m.name); o.put("note", m.note);
                o.put("langs", m.langs); o.put("custom", m.custom); o.put("approx", m.approx);
                o.put("selected", m.id.equals(selectedId(m.kind)));
                if (j != null) { o.put("state", "downloading"); o.put("done", j.done); o.put("total", j.total); }
                else if (ready(m)) { o.put("state", "ready"); o.put("done", have); o.put("total", have); }
                else if (have > 0) { o.put("state", "partial"); o.put("done", have); o.put("total", m.approx); }
                else { o.put("state", "none"); o.put("done", 0); o.put("total", m.approx); }
                arr.put(o);
            }
        } catch (Exception ignored) { }
        return arr.toString();
    }

    String addCustom(String name, String url) {
        try {
            URL u = new URL(url.trim());
            String path = u.getPath();
            String file = path.substring(path.lastIndexOf('/') + 1);
            if (!file.toLowerCase().endsWith(".gguf")) return "주소가 .gguf 파일로 끝나야 합니다.";
            String id = "custom-" + Integer.toHexString(url.trim().hashCode());
            JSONArray arr = new JSONArray(prefs.getString("custom", "[]"));
            for (int i = 0; i < arr.length(); i++) if (id.equals(arr.getJSONObject(i).getString("id"))) return "";
            JSONObject o = new JSONObject();
            o.put("id", id); o.put("name", name == null || name.trim().isEmpty() ? file : name.trim());
            o.put("url", url.trim()); o.put("file", "c-" + file);
            arr.put(o);
            prefs.edit().putString("custom", arr.toString()).apply();
            return "";
        } catch (Exception e) {
            return "주소를 확인해 주세요.";
        }
    }

    void delete(String id) {
        cancel(id);
        Model m = find(id);
        if (m == null) return;
        for (int i = 0; i < m.files.length; i++) { fileOf(m, i).delete(); partOf(m, i).delete(); }
        if (m.custom) {
            try {
                JSONArray arr = new JSONArray(prefs.getString("custom", "[]")), out = new JSONArray();
                for (int i = 0; i < arr.length(); i++) if (!id.equals(arr.getJSONObject(i).getString("id"))) out.put(arr.getJSONObject(i));
                prefs.edit().putString("custom", out.toString()).apply();
            } catch (Exception ignored) { }
        }
        notifyState(m, "none", 0, 0, "");
    }

    void cancel(String id) {
        synchronized (jobs) { Job j = jobs.get(id); if (j != null) j.cancel = true; }
    }

    void cancelAll() {
        synchronized (jobs) { for (Job j : jobs.values()) j.cancel = true; }
    }

    private void notifyState(Model m, String state, long done, long total, String msg) {
        try {
            JSONObject o = new JSONObject();
            o.put("id", m.id); o.put("kind", m.kind); o.put("state", state); o.put("done", done); o.put("total", total); o.put("msg", msg);
            act.emit("onModel", o.toString());
        } catch (Exception ignored) { }
    }

    void download(final String id) {
        final Model m = find(id);
        if (m == null) return;
        final Job job = new Job();
        synchronized (jobs) {
            if (jobs.containsKey(id)) return;
            jobs.put(id, job);
        }
        new Thread(new Runnable() {
            @Override public void run() { fetchAll(m, job); }
        }, "model-download").start();
    }

    private void fetchAll(Model m, Job job) {
        String err = "";
        boolean ok = false;
        act.keepAwake("download", true);
        try {
            job.total = Math.max(m.approx, have(m));
            for (int i = 0; i < m.files.length; i++) {
                if (fileOf(m, i).exists()) continue;
                long before = have(m) - (partOf(m, i).exists() ? partOf(m, i).length() : 0);
                fetch(m, i, job, before);
            }
            ok = true;
        } catch (InterruptedException e) {
            err = "취소했습니다";
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "download", t);
            err = t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage();
        } finally {
            synchronized (jobs) { jobs.remove(m.id); }
            act.keepAwake("download", false);
        }
        long have = have(m);
        if (ok) notifyState(m, "ready", have, have, "");
        else notifyState(m, job.cancel ? "cancelled" : "error", have, job.total, err);
    }

    /** 파일 하나 받기 (끊기면 이어받기). base = 이 파일 앞에 이미 받은 다른 파일들의 크기 */
    private void fetch(Model m, int idx, Job job, long base) throws Exception {
        File part = partOf(m, idx), out = fileOf(m, idx);
        HttpURLConnection c = null;
        try {
            long have = part.exists() ? part.length() : 0;
            String url = m.files[idx][0];
            int code = 0;
            for (int hop = 0; hop < 6; hop++) {       // 다른 서버로 넘기는 주소(리다이렉트)를 따라감
                c = (HttpURLConnection) new URL(url).openConnection();
                c.setInstanceFollowRedirects(false);
                c.setConnectTimeout(20000);
                c.setReadTimeout(30000);
                c.setRequestProperty("User-Agent", "TravelInterpreter-Android");
                c.setRequestProperty("Accept-Encoding", "identity");
                if (have > 0) c.setRequestProperty("Range", "bytes=" + have + "-");
                code = c.getResponseCode();
                if (code >= 300 && code < 400 && c.getHeaderField("Location") != null) {
                    url = new URL(new URL(url), c.getHeaderField("Location")).toString();
                    c.disconnect();
                    continue;
                }
                break;
            }
            if (code == 416) { part.delete(); throw new Exception("이어받기 실패 · 다시 받기를 눌러 주세요"); }
            if (code != 200 && code != 206) throw new Exception("서버 응답 " + code);
            if (code == 200) have = 0;                  // 서버가 이어받기를 안 받아 줌 → 처음부터
            long len = c.getContentLengthLong();
            StatFs fs = new StatFs(dir.getPath());
            if (len > 0 && fs.getAvailableBytes() < len + 200L * 1024 * 1024)
                throw new Exception("저장 공간이 부족합니다 (" + (len / 1024 / 1024 + 200) + "MB 필요)");
            long fileTotal = len > 0 ? have + len : 0;
            job.done = base + have;
            notifyState(m, "downloading", job.done, job.total, "");
            InputStream in = c.getInputStream();
            RandomAccessFile raf = new RandomAccessFile(part, "rw");
            long got = have;
            try {
                raf.setLength(have);
                raf.seek(have);
                byte[] buf = new byte[256 * 1024];
                long lastNote = 0;
                int n;
                while ((n = in.read(buf)) > 0) {
                    if (job.cancel) throw new InterruptedException();
                    raf.write(buf, 0, n);
                    got += n;
                    job.done = base + got;
                    if (job.done > job.total) job.total = job.done;
                    long now = System.currentTimeMillis();
                    if (now - lastNote > 700) { lastNote = now; notifyState(m, "downloading", job.done, job.total, ""); }
                }
            } finally {
                try { raf.close(); } catch (Exception ignored) { }
                try { in.close(); } catch (Exception ignored) { }
            }
            if (fileTotal > 0 && got < fileTotal) throw new Exception("받다가 끊겼습니다 · 다시 누르면 이어서 받습니다");
            if ("gguf".equals(m.type) || "chat".equals(m.type)) {              // GGUF 파일이 맞는지 확인
                byte[] magic = new byte[4];
                FileInputStream fi = new FileInputStream(part);
                try { if (fi.read(magic) < 4) magic[0] = 0; } finally { fi.close(); }
                if (!(magic[0] == 'G' && magic[1] == 'G' && magic[2] == 'U' && magic[3] == 'F')) {
                    part.delete();
                    throw new Exception("받은 파일이 AI 모델(GGUF)이 아닙니다 · 주소를 확인해 주세요");
                }
            } else if (got < 1000) {
                part.delete();
                throw new Exception("받은 파일이 올바르지 않습니다");
            }
            if (!part.renameTo(out)) throw new Exception("파일을 저장하지 못했습니다");
        } finally {
            if (c != null) try { c.disconnect(); } catch (Exception ignored) { }
        }
    }
}
