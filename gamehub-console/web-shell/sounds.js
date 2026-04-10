let audioCtx;

function createCtx() {
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext;

  if (!AudioContextCtor) {
    throw new Error("Web Audio API is not supported in this browser.");
  }

  return new AudioContextCtor();
}

export async function getCtx() {
  if (!audioCtx) {
    audioCtx = createCtx();
  }

  if (audioCtx.state === "suspended") {
    try {
      await audioCtx.resume();
    } catch (error) {
      console.warn("AudioContext resume was blocked.", error);
    }
  }

  return audioCtx;
}

function scheduleTone(ctx, options) {
  const {
    startAt = ctx.currentTime + 0.001,
    frequency,
    endFrequency = frequency,
    type = "sine",
    peak = 0.04,
    attack = 0.008,
    decay = 0.11,
  } = options;
  const floor = 0.0001;
  const attackAt = startAt + attack;
  const endAt = attackAt + decay;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = type;
  osc.frequency.setValueAtTime(frequency, startAt);
  if (endFrequency !== frequency) {
    osc.frequency.linearRampToValueAtTime(endFrequency, endAt);
  }

  gain.gain.setValueAtTime(floor, startAt);
  gain.gain.linearRampToValueAtTime(peak, attackAt);
  gain.gain.exponentialRampToValueAtTime(floor, endAt);

  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(startAt);
  osc.stop(endAt + 0.02);
  osc.addEventListener(
    "ended",
    () => {
      osc.disconnect();
      gain.disconnect();
    },
    { once: true }
  );

  return endAt;
}

export async function playScroll(direction) {
  const ctx = await getCtx();
  const isUp = direction === "up" || direction === -1;

  scheduleTone(ctx, {
    frequency: isUp ? 560 : 420,
    endFrequency: isUp ? 610 : 380,
    type: "triangle",
    peak: 0.024,
    attack: 0.004,
    decay: 0.055,
  });
}

export async function playConfirm() {
  const ctx = await getCtx();
  const startAt = ctx.currentTime + 0.001;

  scheduleTone(ctx, {
    startAt,
    frequency: 520,
    endFrequency: 600,
    type: "sine",
    peak: 0.04,
    attack: 0.008,
    decay: 0.1,
  });

  scheduleTone(ctx, {
    startAt: startAt + 0.06,
    frequency: 780,
    endFrequency: 860,
    type: "sine",
    peak: 0.035,
    attack: 0.008,
    decay: 0.12,
  });
}

export async function playBack() {
  const ctx = await getCtx();

  scheduleTone(ctx, {
    frequency: 540,
    endFrequency: 300,
    type: "triangle",
    peak: 0.035,
    attack: 0.006,
    decay: 0.16,
  });
}

export async function playBookmark(isAdding) {
  const ctx = await getCtx();
  const startAt = ctx.currentTime + 0.001;
  const first = isAdding ? 620 : 460;
  const second = isAdding ? 760 : 360;

  scheduleTone(ctx, {
    startAt,
    frequency: first,
    endFrequency: first + (isAdding ? 20 : -20),
    type: "triangle",
    peak: 0.028,
    attack: 0.005,
    decay: 0.06,
  });

  scheduleTone(ctx, {
    startAt: startAt + 0.05,
    frequency: second,
    endFrequency: second + (isAdding ? 30 : -30),
    type: "triangle",
    peak: 0.026,
    attack: 0.005,
    decay: 0.065,
  });
}

export async function playPlay() {
  const ctx = await getCtx();

  scheduleTone(ctx, {
    frequency: 180,
    endFrequency: 880,
    type: "square",
    peak: 0.03,
    attack: 0.003,
    decay: 0.12,
  });
}

export async function playRefresh() {
  const ctx = await getCtx();
  const startAt = ctx.currentTime + 0.001;

  [420, 560, 720].forEach((frequency, index) => {
    scheduleTone(ctx, {
      startAt: startAt + index * 0.045,
      frequency,
      endFrequency: frequency + 35,
      type: "triangle",
      peak: 0.03,
      attack: 0.005,
      decay: 0.07,
    });
  });
}

export async function playTab() {
  const ctx = await getCtx();

  scheduleTone(ctx, {
    frequency: 680,
    endFrequency: 640,
    type: "sine",
    peak: 0.018,
    attack: 0.003,
    decay: 0.04,
  });
}
