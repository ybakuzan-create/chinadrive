document.addEventListener("DOMContentLoaded", () => {
  const status = JSON.parse(localStorage.getItem("playerStatus")) || { 力: 0, 魂: 0, 気: 0 };
  const logArea = document.querySelector(".log-area");

  function addLog(text) {
    logArea.innerHTML += `🗡️ ${text}<br>`;
    logArea.scrollTop = logArea.scrollHeight;
  }

  function evaluateBattle(choice) {
    const { 力, 魂, 気 } = status;

    if (choice === "こうげき") {
      if (力 >= 20) {
        addLog("強力な攻撃が魔王を貫いた！勝利が近い！");
      } else {
        addLog("攻撃は当たったが、ダメージは小さい…");
      }
    } else if (choice === "とくしゅ") {
      if (魂 >= 15 && 気 >= 10) {
        addLog("魂と気を高め、強力な術を放った！魔王は苦しんでいる！");
      } else {
        addLog("術を唱えたが力が足りず、不発に終わった…");
      }
    } else if (choice === "ぼうぎょ") {
      if (気 >= 10) {
        addLog("集中して守りを固めた！魔王の攻撃を防いだ！");
      } else {
        addLog("防御したが、力が足りず貫かれた…");
      }
    }
  }

  // 各ボタンに処理をバインド
  document.getElementById("btn-attack").addEventListener("click", () => {
    evaluateBattle("こうげき");
  });

  document.getElementById("btn-special").addEventListener("click", () => {
    evaluateBattle("とくしゅ");
  });

  document.getElementById("btn-defend").addEventListener("click", () => {
    evaluateBattle("ぼうぎょ");
  });

  // 初期ログ
  addLog("🔥 魔王が現れた！リンファは戦いに挑む！");
});
