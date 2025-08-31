document.addEventListener("DOMContentLoaded", () => {
  const logArea = document.querySelector(".log-area");
  const statusElements = {
    力: document.querySelector(".status-panel div:nth-child(1)"),
    魂: document.querySelector(".status-panel div:nth-child(2)"),
    気: document.querySelector(".status-panel div:nth-child(3)")
  };

  let status = {
    力: 12,
    魂: 8,
    気: 5
  };

  let currentClass = "少女"; // 初期クラス
  const loopCount = 1;       // 今回は1周目として固定
  let dayCount = 1;
  const maxDays = 14;
  const header = document.querySelector("header");

  function updateStatus() {
    for (const key in status) {
      statusElements[key].textContent = `${key}：${status[key]}`;
    }
    header.textContent = `${dayCount}日目 ／ ${maxDays}日間`;
  }

  function addLog(message) {
    logArea.innerHTML += `📜 ${message}<br>`;
    logArea.scrollTop = logArea.scrollHeight;
  }

  function checkClassChange() {
    const total = status.力 + status.魂 + status.気;
    const sum魂気 = status.魂 + status.気;

    if (loopCount === 1 && currentClass === "少女") {
      if (status.力 >= 15) {
        currentClass = "クンフー少女";
        addLog("🔥 クンフー少女にクラスチェンジした！");
      } else if (status.魂 >= 15) {
        currentClass = "キョンシー";
        addLog("👻 キョンシーにクラスチェンジした！");
      } else if (status.気 >= 15) {
        currentClass = "仙女見習い";
        addLog("🌸 仙女見習いにクラスチェンジした！");
      }
    }
  }

  function saveStatusToStorage() {
    localStorage.setItem("playerStatus", JSON.stringify(status));
    localStorage.setItem("currentClass", currentClass);
  }

  function advanceDay() {
    dayCount++;
    updateStatus();
    saveStatusToStorage();

    if (dayCount > maxDays) {
      setTimeout(() => {
        alert("🔥 魔王戦に突入！");
        window.location.href = "boss.html";
      }, 500);
    }
  }

  // 行動定義
  const actions = {
    "鍛錬（力+3）": () => {
      status.力 += 3;
      addLog("リンファは鍛錬をした（力+3）");
      checkClassChange();
    },
    "瞑想（魂+2, 気+1）": () => {
      status.魂 += 2;
      status.気 += 1;
      addLog("リンファは瞑想をした（魂+2, 気+1）");
      checkClassChange();
    },
    "墓地探索（魂+4）": () => {
      status.魂 += 4;
      addLog("リンファは墓地を探索した（魂+4）");
      checkClassChange();
    }
  };

  // モーダル行動選択
  document.querySelectorAll(".modal-option").forEach(el => {
    el.addEventListener("click", () => {
      const text = el.textContent.trim();
      if (actions[text]) {
        actions[text]();
        updateStatus();
        advanceDay();
      }
      document.getElementById("modalToggle").checked = false;
    });
  });

  // 「休む」ボタン処理
  document.querySelectorAll(".action-button")[1].addEventListener("click", () => {
    status.気 += 2;
    addLog("リンファは休んだ（気+2）");
    updateStatus();
    advanceDay();
  });

  updateStatus();
});
