/* 键盘 + 鼠标输入。
 * 键盘：WASD/方向键移动，Space 跳，Shift 跑，E 交互，Esc 取消。
 * 鼠标：左键拖拽转视角（累积增量由主循环消费），滚轮缩放，右键点地（NDC 队列）。 */
export class Input {
  constructor() {
    this.keys = new Set();
    this.jumpQueued = false;
    this.interactQueued = false;
    this.cancelQueued = false;

    // 指针状态
    this.dragging = false;
    this.dragPointerId = -1;
    this.lastX = 0;
    this.lastY = 0;
    this.dragDX = 0;
    this.dragDY = 0;
    this.wheelDY = 0;
    this.groundClicks = []; // 右键点地：{x, y} 为 NDC 坐标（x 右、y 上）

    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      this.keys.add(e.code);
      if (e.code === 'Space') {
        this.jumpQueued = true;
        e.preventDefault();
      }
      if (e.code === 'KeyE') this.interactQueued = true;
      if (e.code === 'Escape') this.cancelQueued = true;
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => {
      this.keys.clear();
      this.dragging = false;
      this.dragPointerId = -1;
    });
  }

  /* 绑定到 renderer 的 canvas（需在 WebGL renderer 创建后调用） */
  attach(el) {
    el.addEventListener('contextmenu', (e) => e.preventDefault());

    el.addEventListener('pointerdown', (e) => {
      if (e.button === 0 && !this.dragging) {
        this.dragging = true;
        this.dragPointerId = e.pointerId;
        this.lastX = e.clientX;
        this.lastY = e.clientY;
        el.setPointerCapture?.(e.pointerId);
      } else if (e.button === 2) {
        const rect = el.getBoundingClientRect();
        this.groundClicks.push({
          x: ((e.clientX - rect.left) / rect.width) * 2 - 1,
          y: -((e.clientY - rect.top) / rect.height) * 2 + 1,
        });
      }
    });

    el.addEventListener('pointermove', (e) => {
      if (!this.dragging || e.pointerId !== this.dragPointerId) return;
      this.dragDX += e.clientX - this.lastX;
      this.dragDY += e.clientY - this.lastY;
      this.lastX = e.clientX;
      this.lastY = e.clientY;
    });

    // pointerup 有 button 需判左键；pointercancel 不带可信 button，只按 pointerId 配对
    el.addEventListener('pointerup', (e) => {
      if (e.pointerId === this.dragPointerId && e.button === 0) {
        this.dragging = false;
        this.dragPointerId = -1;
      }
    });
    el.addEventListener('pointercancel', (e) => {
      if (e.pointerId === this.dragPointerId) {
        this.dragging = false;
        this.dragPointerId = -1;
      }
    });

    el.addEventListener('wheel', (e) => {
      // Firefox deltaMode=1 单位是行（≈33px/行），统一换算成像素增量
      const dy = e.deltaMode === 1 ? e.deltaY * 33 : e.deltaY;
      this.wheelDY += dy;
      e.preventDefault();
    }, { passive: false });
  }

  /* 输入轴：x 右为正，y 前为正 */
  get axis() {
    const k = this.keys;
    const x = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    const y = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    return { x, y };
  }

  get running() {
    return this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
  }

  /* 取走本帧鼠标拖拽累积量（左键转视角） */
  takeDrag() {
    const d = { dx: this.dragDX, dy: this.dragDY };
    this.dragDX = 0;
    this.dragDY = 0;
    return d;
  }

  /* 取走本帧滚轮累积量 */
  takeWheel() {
    const w = this.wheelDY;
    this.wheelDY = 0;
    return w;
  }

  /* 取出最早一个右键点地坐标，没有则 null */
  takeGroundClick() {
    return this.groundClicks.shift() ?? null;
  }

  /* 跳跃为边沿触发：取走一次即清 */
  takeJump() {
    const j = this.jumpQueued;
    this.jumpQueued = false;
    return j;
  }

  takeInteract() {
    const v = this.interactQueued;
    this.interactQueued = false;
    return v;
  }

  takeCancel() {
    const v = this.cancelQueued;
    this.cancelQueued = false;
    return v;
  }

  /* 非玩法分支（旅行过场/星图/对话）里清空全部边沿，避免陈旧输入跨状态误触发 */
  flush() {
    this.jumpQueued = false;
    this.interactQueued = false;
    this.cancelQueued = false;
    this.groundClicks.length = 0;
    this.dragDX = 0;
    this.dragDY = 0;
    this.wheelDY = 0;
  }
}
