package kr.pureun.travel;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

/**
 * 폰 안의 무거운 일(받아 적기 · 번역)을 한 번에 하나씩 차례로 하게 하는 줄.
 * 둘이 동시에 돌면 서로 CPU를 뺏어 둘 다 느려지므로, 온 차례대로 번갈아 한다 (순수 자바).
 */
final class Heavy {
    private static final ReentrantLock LOCK = new ReentrantLock(true);   // 온 순서대로
    private Heavy() { }

    /** 차례를 기다림. 너무 오래(maxMs) 기다리면 그냥 진행 (멈춰 버리는 일이 없게). 차례를 얻었으면 true → 끝나고 done() */
    static boolean enter(long maxMs) {
        try { return LOCK.tryLock(maxMs, TimeUnit.MILLISECONDS); }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); return false; }
    }

    static void done(boolean entered) {
        if (entered && LOCK.isHeldByCurrentThread()) LOCK.unlock();
    }
}
