/* 对话面板：靠近 NPC 按 E 开始，E/Space/点击逐句推进，Esc 结束。
 * 打字机逐字显现；未打完时按一次补全整句，再按一次才进下一句。 */
import { DIALOGUES } from './dialogues.js';

const TYPE_CPS = 26; // 每秒显现字符数（中文按字计）

export class DialogueUI {
  constructor() {
    this.el = document.getElementById('dialogue');
    this.speakerEl = document.getElementById('dialogue-speaker');
    this.textEl = document.getElementById('dialogue-text');
    this.nextEl = document.getElementById('dialogue-next');
    this.el.querySelector('.dialogue-card')
      .addEventListener('click', () => this.advance());
    this.active = false;
    this.npc = null;
    this.lines = [];
    this.index = 0;
    this.shown = 0;
  }

  start(npc) {
    const data = DIALOGUES[npc.key];
    if (!data) {
      console.warn(`没有为 NPC "${npc.key}" 配置对话`);
      return;
    }
    this.active = true;
    this.npc = npc;
    this.lines = data.lines;
    this.index = 0;
    this.el.classList.remove('hidden');
    this.renderLine();
  }

  close() {
    this.active = false;
    this.npc = null;
    this.el.classList.add('hidden');
  }

  /* 由主循环每帧调用；仅在对话中消费交互/取消边沿 */
  update(dt, input) {
    if (!this.active) return;
    const cur = this.lines[this.index];
    if (this.shown < cur.t.length) {
      this.shown = Math.min(cur.t.length, this.shown + TYPE_CPS * dt);
      this.textEl.textContent = cur.t.slice(0, Math.ceil(this.shown));
    }
    this.nextEl.style.visibility = this.shown >= cur.t.length ? 'visible' : 'hidden';
    if (input.takeCancel()) {
      this.close();
      return;
    }
    if (input.takeInteract() || input.takeJump()) this.advance();
  }

  advance() {
    if (!this.active) return;
    const cur = this.lines[this.index];
    if (this.shown < cur.t.length) {
      this.shown = cur.t.length; // 第一次按键：补全整句
      this.textEl.textContent = cur.t;
      this.nextEl.style.visibility = 'visible';
      return;
    }
    this.index += 1;
    if (this.index >= this.lines.length) {
      this.close();
    } else {
      this.renderLine(false);
    }
  }

  renderLine() {
    const line = this.lines[this.index];
    this.textEl.className = 'who-' + line.who;
    this.speakerEl.className = 'speaker who-' + line.who;
    this.speakerEl.textContent = line.who === 'p' ? '小王子'
      : line.who === 'x' ? '' : this.npc.label;
    if (line.who === 'x') this.speakerEl.textContent = '·';
    this.shown = 0;
    this.textEl.textContent = '';
    this.nextEl.style.visibility = 'hidden';
  }
}
