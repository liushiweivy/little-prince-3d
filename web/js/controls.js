/* 键盘输入：WASD/方向键移动，Space 跳，Shift 跑 */
export class Input {
  constructor() {
    this.keys = new Set();
    this.jumpQueued = false;
    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      this.keys.add(e.code);
      if (e.code === 'Space') {
        this.jumpQueued = true;
        e.preventDefault();
      }
    });
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());
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

  /* 跳跃为边沿触发：取走一次即清 */
  takeJump() {
    const j = this.jumpQueued;
    this.jumpQueued = false;
    return j;
  }
}
