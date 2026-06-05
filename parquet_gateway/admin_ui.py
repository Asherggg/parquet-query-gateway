from __future__ import annotations


ADMIN_CONFIG_UI_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Parquet Gateway Config</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #64717f;
      --line: #d9e0e8;
      --blue: #155dfc;
      --green: #137a41;
      --red: #ba1a1a;
      --yellow: #8a5a00;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); }
    header {
      height: 56px; display: flex; align-items: center; gap: 16px; padding: 0 18px;
      border-bottom: 1px solid var(--line); background: var(--panel); position: sticky; top: 0; z-index: 2;
    }
    h1 { font-size: 17px; margin: 0; font-weight: 700; }
    .token { flex: 1; display: flex; align-items: center; gap: 8px; min-width: 240px; }
    input, textarea, select {
      border: 1px solid var(--line); border-radius: 6px; background: white; color: var(--ink);
      font: inherit; padding: 8px 10px; min-width: 0;
    }
    .token input { width: 100%; }
    button {
      border: 1px solid var(--line); border-radius: 6px; background: white; color: var(--ink);
      font: inherit; padding: 8px 11px; cursor: pointer; white-space: nowrap;
    }
    button.primary { background: var(--blue); border-color: var(--blue); color: white; }
    button.danger { color: var(--red); }
    main { display: grid; grid-template-columns: minmax(380px, 46%) 1fr; gap: 14px; padding: 14px; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; min-height: calc(100vh - 84px); overflow: hidden; }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 12px; border-bottom: 1px solid var(--line); }
    .panel-title { font-weight: 700; font-size: 14px; }
    .yaml { width: 100%; min-height: calc(100vh - 144px); border: 0; border-radius: 0; resize: vertical; font: 13px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; padding: 12px; }
    .tabs { display: flex; gap: 6px; padding: 10px 12px 0; }
    .tab { padding: 7px 10px; border: 1px solid var(--line); border-bottom: 0; border-radius: 6px 6px 0 0; color: var(--muted); }
    .tab.active { color: var(--ink); background: #eef3ff; border-color: #b8c9ff; }
    .view { display: none; padding: 12px; }
    .view.active { display: block; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 12px; }
    label span { color: var(--muted); }
    label input, label textarea { width: 100%; color: var(--ink); }
    .row { display: flex; align-items: center; gap: 8px; }
    .row > * { flex: 1; }
    .card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 10px; background: white; }
    .card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
    .card-title { font-weight: 700; font-size: 14px; overflow-wrap: anywhere; }
    .muted { color: var(--muted); font-size: 12px; }
    .status { font-size: 13px; min-width: 210px; color: var(--muted); }
    .status.ok { color: var(--green); }
    .status.err { color: var(--red); }
    .pill { display: inline-flex; align-items: center; padding: 2px 7px; border: 1px solid var(--line); border-radius: 999px; font-size: 12px; color: var(--muted); margin: 2px; }
    .toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .role-dropdown { position: relative; width: 100%; }
    .role-dropdown-toggle {
      width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 8px;
      text-align: left; min-height: 36px; color: var(--ink);
    }
    .role-dropdown-toggle::after { content: "v"; color: var(--muted); font-size: 11px; }
    .role-dropdown-menu {
      display: none; position: absolute; z-index: 5; left: 0; right: 0; top: calc(100% + 4px);
      max-height: 220px; overflow: auto; padding: 6px; border: 1px solid var(--line);
      border-radius: 6px; background: white; box-shadow: 0 10px 24px rgb(23 32 42 / 12%);
    }
    .role-dropdown.open .role-dropdown-menu { display: grid; gap: 2px; }
    .role-option {
      display: flex; align-items: center; gap: 8px; padding: 6px 7px; border-radius: 5px;
      color: var(--ink); font-size: 13px; cursor: pointer;
    }
    .role-option:hover { background: #f2f5f9; }
    .role-option input { width: auto; }
    .workspace-note { margin-bottom: 10px; padding: 9px 10px; border: 1px solid #d8e2f4; border-radius: 6px; background: #f7faff; color: var(--muted); font-size: 12px; }
    .field-permission-matrix { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }
    .field-permission-matrix th, .field-permission-matrix td { border: 1px solid var(--line); padding: 6px; text-align: center; }
    .field-permission-matrix th:first-child, .field-permission-matrix td:first-child { text-align: left; min-width: 160px; }
    .field-permission-matrix th { background: #f8fafc; color: var(--muted); font-weight: 650; }
    .matrix-cell { width: 16px; height: 16px; }
    .matrix-actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
    .card-toggle { text-align: left; border: 0; padding: 0; background: transparent; white-space: normal; }
    .card-toggle::before { content: "v"; display: inline-block; margin-right: 6px; color: var(--muted); }
    .collapsed .card-toggle::before { content: ">"; }
    .dataset-body, .discovered-body { margin-top: 10px; }
    .collapsed .dataset-body, .collapsed .discovered-body { display: none; }
    .summary-line { color: var(--muted); font-size: 12px; margin-top: 3px; }
    .section-label { color: var(--muted); font-size: 12px; font-weight: 700; margin: 0 0 8px; }
    .candidate-card { border-left: 4px solid #7aa7d9; background: #f8fbff; }
    .candidate-card .card-head { align-items: center; }
    .candidate-badge, .permission-badge { border-radius: 999px; font-size: 12px; font-weight: 700; padding: 3px 8px; white-space: nowrap; }
    .candidate-badge { background: #e8f2ff; color: #245f99; border: 1px solid #bfd8f3; }
    .permission-card { border-left: 4px solid var(--green); }
    .permission-card .card-head { align-items: center; }
    .permission-badge { background: #eaf7ef; color: var(--green); border: 1px solid #b8dfc5; }
    .quick-copy-list { display: grid; grid-template-columns: minmax(120px, 150px) minmax(120px, 150px) auto; gap: 6px; align-items: center; }
    .quick-copy-list select { width: 100%; padding: 6px 8px; font-size: 12px; }
    .quick-copy-list button { padding: 6px 9px; font-size: 12px; }
    .row-policy-editor { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--line); }
    .user-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .user-table th, .user-table td { border-bottom: 1px solid var(--line); padding: 7px; vertical-align: top; }
    .user-table th { color: var(--muted); text-align: left; font-weight: 650; background: #f8fafc; }
    .user-table input { width: 100%; }
    .advanced-yaml-panel { display: grid; gap: 10px; }
    .hidden { display: none; }
    @media (max-width: 980px) {
      header { height: auto; flex-wrap: wrap; padding: 12px; }
      main { grid-template-columns: 1fr; }
      .panel { min-height: auto; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Parquet Gateway Config</h1>
    <div class="token">
      <input id="token" type="password" autocomplete="off" placeholder="Admin bearer token" />
      <button id="load">加载</button>
    </div>
    <div id="status" class="status">未加载</div>
  </header>
  <main>
    <section class="panel">
      <div class="panel-head">
        <div>
          <div class="panel-title">YAML</div>
          <div id="path" class="muted"></div>
        </div>
        <div class="toolbar">
          <button id="copy">复制</button>
          <button id="save" class="primary">保存</button>
        </div>
      </div>
      <textarea id="yaml" class="yaml" spellcheck="false"></textarea>
    </section>
    <section class="panel">
      <div class="tabs">
        <button class="tab active" data-tab="datasets">数据集</button>
        <button class="tab" data-tab="users">用户</button>
        <button class="tab" data-tab="pending">待审批</button>
        <button class="tab" data-tab="settings">基础配置</button>
        <button class="tab" data-tab="advanced-yaml">YAML 高级</button>
      </div>
      <div id="datasets" class="view active">
        <div class="toolbar" style="margin-bottom:10px">
          <button id="discover-datasets">扫描 Parquet 数据表</button>
          <button id="sync-datasets">同步字段权限到 YAML</button>
          <button id="expand-all-datasets">全部展开</button>
          <button id="collapse-all-datasets">全部折叠</button>
        </div>
        <div id="discovered-datasets"></div>
        <div class="section-label">权限配置工作区</div>
        <div id="dataset-list"></div>
      </div>
      <div id="users" class="view">
        <div class="workspace-note">飞书用户在这里维护角色和 attributes；左侧 YAML 会随视觉表单同步。</div>
        <div class="card">
          <div class="grid">
            <label><span>App ID</span><input id="feishu-app-id" /></label>
            <label><span>Redirect URI</span><input id="feishu-redirect-uri" /></label>
            <label><span>Enabled</span><select id="feishu-enabled"><option value="true">true</option><option value="false">false</option></select></label>
            <label><span>App Secret</span><input value="********" disabled /></label>
          </div>
        </div>
        <div class="toolbar" style="margin-bottom:10px">
          <button id="add-user">新增用户</button>
          <button id="sync-users">同步到 YAML</button>
        </div>
        <div id="user-list"></div>
      </div>
      <div id="pending" class="view">
        <div class="workspace-note">待审批飞书用户来自登录成功但尚未授权的身份。批准后默认 analyst，可在用户页继续调整。</div>
        <div id="pending-users"></div>
      </div>
      <div id="legacy-feishu" class="view hidden">
        <button class="tab" data-tab="feishu">飞书用户</button>
        <button class="tab" data-tab="datasets">数据集</button>
        <button class="tab" data-tab="settings">基础配置</button>
      </div>
      <div id="settings" class="view">
        <div class="card">
          <div class="grid">
            <label><span>data_root</span><input id="data-root" /></label>
            <label><span>max_limit</span><input id="max-limit" type="number" min="1" /></label>
            <label><span>default_limit</span><input id="default-limit" type="number" min="1" /></label>
            <label><span>query_timeout_seconds</span><input id="timeout" type="number" min="1" /></label>
          </div>
          <div class="toolbar" style="margin-top:10px"><button id="sync-settings">同步到 YAML</button></div>
        </div>
      </div>
      <div id="advanced-yaml" class="view">
        <div class="advanced-yaml-panel">
          <div class="workspace-note">YAML 是高级兜底入口。手动修改后，点击“应用 YAML 到表单”才会重渲染视觉工作区。</div>
          <div class="toolbar">
            <button id="apply-yaml">应用 YAML 到表单</button>
            <button id="preview-diff">预览差异</button>
          </div>
          <div id="yaml-apply-message" class="muted"></div>
        </div>
      </div>
    </section>
  </main>
  <template id="user-template">
    <div class="card user-card">
      <div class="card-head">
        <div class="card-title user-title">用户</div>
        <button class="danger remove-user">删除</button>
      </div>
      <div class="grid">
        <label><span>name</span><input class="user-name" placeholder="飞书姓名" /></label>
        <label><span>open_id（可选）</span><input class="user-open-id" placeholder="管理员可后续补充" /></label>
        <label><span>id</span><input class="user-id" placeholder="内部用户 ID" /></label>
        <label><span>roles</span><div class="user-roles"></div></label>
      </div>
      <div class="muted" style="margin-top:10px">attributes</div>
      <div class="user-attribute-fields grid"></div>
      <details style="margin-top:10px">
        <summary class="muted">高级 JSON</summary>
        <textarea class="user-attributes" rows="3">{}</textarea>
      </details>
    </div>
  </template>
  <script>
    let config = null;
    const expandedDatasetIds = new Set();
    const DEFAULT_ROLES = ["analyst", "admin", "finance", "operations", "promotion", "warehouse", "hr"];
    const ROLE_LABELS = {
      analyst: "分析师",
      admin: "管理员",
      finance: "财务",
      operations: "运营",
      promotion: "推广",
      warehouse: "仓储",
      hr: "人事",
    };
    const $ = (id) => document.getElementById(id);
    const token = () => $("token").value.trim().replace(/^Bearer\s+/i, "").replace(/^["']|["']$/g, "").trim();
    const setStatus = (text, cls = "") => { $("status").className = "status " + cls; $("status").textContent = text; };
    const authHeaders = () => token() ? { Authorization: "Bearer " + token() } : {};
    const splitList = (value) => value.split(",").map((v) => v.trim()).filter(Boolean);
    const dump = (obj) => jsyamlDump(obj);
    const errorMessage = (err, fallback) => err?.message ? `${fallback}: ${err.message}` : fallback;

    async function readJsonResponse(res) {
      const text = await res.text();
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch {
        throw new Error(`服务器返回了非 JSON 响应，HTTP ${res.status}`);
      }
    }

    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".tab,.view").forEach((el) => el.classList.remove("active"));
        tab.classList.add("active");
        $(tab.dataset.tab).classList.add("active");
      });
    });

    $("load").addEventListener("click", loadConfig);
    $("save").addEventListener("click", saveConfig);
    $("copy").addEventListener("click", async () => { await navigator.clipboard.writeText($("yaml").value); setStatus("已复制 YAML", "ok"); });
    $("apply-yaml").addEventListener("click", applyYamlToForm);
    $("preview-diff").addEventListener("click", () => setStatus("当前版本会在保存前根据视觉表单重新生成 YAML", "ok"));
    $("add-user").addEventListener("click", () => {
      addUserCard({ roles: ["analyst"], attributes: {} });
      syncUsersFromForm();
      renderYaml();
    });
    $("sync-users").addEventListener("click", () => { syncUsersFromForm(); renderYaml(); setStatus("用户已同步到 YAML", "ok"); });
    $("sync-settings").addEventListener("click", () => { syncSettingsFromForm(); renderYaml(); setStatus("基础配置已同步到 YAML", "ok"); });
    $("discover-datasets").addEventListener("click", discoverDatasets);
    $("sync-datasets").addEventListener("click", () => { syncDatasetsFromForm(); renderYaml(); setStatus("字段权限已同步到 YAML", "ok"); });
    $("expand-all-datasets").addEventListener("click", () => {
      document.querySelectorAll(".dataset-card").forEach((card) => { expandedDatasetIds.add(card.dataset.datasetId); card.classList.remove("collapsed"); });
      document.querySelectorAll(".discovered-card").forEach((card) => card.classList.remove("collapsed"));
    });
    $("collapse-all-datasets").addEventListener("click", () => {
      document.querySelectorAll(".dataset-card").forEach((card) => { expandedDatasetIds.delete(card.dataset.datasetId); card.classList.add("collapsed"); });
      document.querySelectorAll(".discovered-card").forEach((card) => card.classList.add("collapsed"));
    });
    $("feishu-app-id").addEventListener("input", syncFeishuForm);
    $("feishu-redirect-uri").addEventListener("input", syncFeishuForm);
    $("feishu-enabled").addEventListener("change", syncFeishuForm);

    async function loadConfig() {
      if (!token()) { setStatus("请输入 admin token", "err"); return; }
      setStatus("加载中...");
      try {
        const res = await fetch("/admin/config", { headers: authHeaders() });
        const body = await readJsonResponse(res);
        if (!res.ok) { setStatus(body.error?.message || "加载失败", "err"); return; }
        config = body.config;
        $("path").textContent = body.path;
        renderAll();
        setStatus("已加载", "ok");
      } catch (err) {
        setStatus(errorMessage(err, "加载失败"), "err");
      }
    }

    async function saveConfig() {
      if (!token()) { setStatus("请输入 admin token", "err"); return; }
      syncAllFromForms();
      const validationErrors = validateBeforeSave();
      if (validationErrors.length) {
        setStatus(validationErrors[0], "err");
        return;
      }
      renderYaml();
      const saveButton = $("save");
      saveButton.disabled = true;
      setStatus("保存中...");
      try {
        const res = await fetch("/admin/config", {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ yaml: $("yaml").value }),
        });
        const body = await readJsonResponse(res);
        if (!res.ok) { setStatus(body.error?.message || "保存失败", "err"); return; }
        setStatus("已保存，备份 " + body.backup_path, "ok");
        await loadConfig();
      } catch (err) {
        setStatus(errorMessage(err, "保存失败"), "err");
      } finally {
        saveButton.disabled = false;
      }
    }

    function renderAll() {
      renderFeishu();
      renderPendingUsers();
      renderUsers();
      renderDatasets();
      renderSettings();
      renderYaml();
    }

    function renderFeishu() {
      const feishu = config.auth?.feishu || {};
      $("feishu-app-id").value = feishu.app_id || "";
      $("feishu-redirect-uri").value = feishu.redirect_uri || "";
      $("feishu-enabled").value = String(Boolean(feishu.enabled));
    }

    function renderUsers() {
      $("user-list").innerHTML = "";
      (config.auth?.feishu_users || []).forEach(addUserCard);
    }

    function renderPendingUsers() {
      const wrap = $("pending-users");
      const pending = config.auth?.pending_feishu_users || [];
      wrap.innerHTML = "";
      if (!pending.length) return;
      const heading = document.createElement("div");
      heading.className = "muted";
      heading.style.margin = "0 0 8px";
      heading.textContent = "Pending Feishu users";
      wrap.appendChild(heading);
      pending.forEach((user, index) => {
        const card = document.createElement("div");
        card.className = "card pending-card";
        card.innerHTML = `
          <div class="card-head">
            <div>
              <div class="card-title"></div>
              <div class="muted"></div>
            </div>
            <button type="button" class="approve-pending">Approve</button>
          </div>
        `;
        card.querySelector(".card-title").textContent = user.name || user.open_id || "Pending user";
        card.querySelector(".muted").textContent = user.open_id || "";
        card.querySelector(".approve-pending").addEventListener("click", () => approvePendingUser(index));
        wrap.appendChild(card);
      });
    }

    function approvePendingUser(index) {
      config.auth ||= {};
      config.auth.pending_feishu_users ||= [];
      const pendingUser = config.auth.pending_feishu_users[index];
      if (!pendingUser) return;
      addUserCard({
        open_id: pendingUser.open_id || "",
        name: pendingUser.name || "",
        id: readableInternalId(pendingUser.name, pendingUser.open_id),
        roles: ["analyst"],
        attributes: {},
      });
      config.auth.pending_feishu_users.splice(index, 1);
      syncUsersFromForm();
      renderPendingUsers();
      renderYaml();
      setStatus("Pending Feishu user approved into YAML", "ok");
    }

    function addUserCard(user) {
      const node = $("user-template").content.firstElementChild.cloneNode(true);
      node.querySelector(".user-open-id").value = user.open_id || "";
      node.querySelector(".user-name").value = user.name || "";
      node.querySelector(".user-id").value = user.id || "";
      const syncUserCard = () => {
        updateTitle();
        syncUsersFromForm();
        renderYaml();
      };
      renderRoleDropdown(node.querySelector(".user-roles"), user.roles || [], syncUserCard);
      renderAttributeFields(node.querySelector(".user-attribute-fields"), user.attributes || {});
      node.querySelector(".user-attributes").value = JSON.stringify(user.attributes || {}, null, 2);
      const updateTitle = () => { node.querySelector(".user-title").textContent = node.querySelector(".user-id").value || node.querySelector(".user-name").value || node.querySelector(".user-open-id").value || "新用户"; };
      node.querySelectorAll("input,textarea").forEach((el) => el.addEventListener("input", syncUserCard));
      node.querySelector(".remove-user").addEventListener("click", () => {
        node.remove();
        syncUsersFromForm();
        renderYaml();
      });
      updateTitle();
      $("user-list").appendChild(node);
    }

    function readableInternalId(name, openId) {
      const ascii = String(name || "")
        .normalize("NFKD")
        .replace(/[^\w\s-]/g, "")
        .trim()
        .replace(/[\s_-]+/g, "_")
        .replace(/^_+|_+$/g, "")
        .toLowerCase();
      return ascii || openId || name || "";
    }

    function knownRoles() {
      const roles = new Set(DEFAULT_ROLES);
      Object.values(config?.datasets || {}).forEach((dataset) => {
        (dataset.roles || []).forEach((role) => roles.add(role));
        Object.keys(dataset.columns || {}).forEach((role) => roles.add(role));
      });
      (config?.auth?.feishu_users || []).forEach((user) => (user.roles || []).forEach((role) => roles.add(role)));
      return Array.from(roles).sort((a, b) => a === "analyst" ? -1 : b === "analyst" ? 1 : a.localeCompare(b));
    }

    function renderRoleDropdown(container, selected, onChange) {
      const selectedSet = new Set(selected || []);
      container.innerHTML = `
        <div class="role-dropdown">
          <button type="button" class="role-dropdown-toggle"></button>
          <div class="role-dropdown-menu">
            ${knownRoles().map((role) => `
              <label class="role-option">
                <input type="checkbox" class="role-check" value="${escapeHtml(role)}" ${selectedSet.has(role) ? "checked" : ""} />
                <span>${escapeHtml(roleLabel(role))}</span>
              </label>
            `).join("")}
          </div>
        </div>
      `;
      const dropdown = container.querySelector(".role-dropdown");
      const toggle = container.querySelector(".role-dropdown-toggle");
      const update = () => {
        const labels = selectedRoles(container).map(roleLabel);
        toggle.textContent = labels.length ? labels.join(", ") : "选择角色";
      };
      toggle.addEventListener("click", () => dropdown.classList.toggle("open"));
      container.querySelectorAll(".role-check").forEach((input) => input.addEventListener("change", () => {
        update();
        if (onChange) onChange();
      }));
      update();
    }

    function selectedRoles(container) {
      return Array.from(container.querySelectorAll(".role-check:checked")).map((input) => input.value);
    }

    function roleLabel(role) {
      return ROLE_LABELS[role] || role;
    }

    function knownAttributeKeys() {
      const keys = new Set();
      Object.values(config?.datasets || {}).forEach((dataset) => {
        const source = dataset.row_policy?.source || "";
        if (source.startsWith("attributes.")) keys.add(source.slice("attributes.".length));
      });
      (config?.auth?.feishu_users || []).forEach((user) => Object.keys(user.attributes || {}).forEach((key) => keys.add(key)));
      return Array.from(keys).sort();
    }

    function renderAttributeFields(container, attributes) {
      const keys = knownAttributeKeys();
      if (!keys.length) {
        container.innerHTML = '<div class="muted">当前数据集没有 row_policy，通常保持 {} 即可。</div>';
        return;
      }
      container.innerHTML = keys.map((key) => {
        const value = attributes?.[key];
        const text = Array.isArray(value) ? value.join(", ") : value == null ? "" : String(value);
        return `<label><span>${escapeHtml(key)}</span><input class="attribute-field" data-key="${escapeHtml(key)}" value="${escapeHtml(text)}" placeholder="多个值用逗号分隔" /></label>`;
      }).join("");
    }

    function syncFeishuForm() {
      if (!config) return;
      config.auth ||= {};
      config.auth.feishu ||= {};
      config.auth.feishu.enabled = $("feishu-enabled").value === "true";
      config.auth.feishu.app_id = $("feishu-app-id").value.trim();
      config.auth.feishu.redirect_uri = $("feishu-redirect-uri").value.trim();
      renderYaml();
    }

    function syncUsersFromForm() {
      config.auth ||= {};
      config.auth.feishu_users = Array.from(document.querySelectorAll(".user-card")).map((node) => {
        let attributes = {};
        try { attributes = JSON.parse(node.querySelector(".user-attributes").value || "{}"); } catch { attributes = {}; }
        node.querySelectorAll(".attribute-field").forEach((input) => {
          const values = splitList(input.value);
          if (values.length) attributes[input.dataset.key] = values;
          else delete attributes[input.dataset.key];
        });
        const user = {
          id: node.querySelector(".user-id").value.trim(),
          roles: selectedRoles(node.querySelector(".user-roles")),
          attributes,
        };
        const openId = node.querySelector(".user-open-id").value.trim();
        const name = node.querySelector(".user-name").value.trim();
        if (openId) user.open_id = openId;
        if (name) user.name = name;
        return user;
      });
    }

    function renderDatasets() {
      const wrap = $("dataset-list");
      wrap.innerHTML = "";
      Object.entries(config.datasets || {}).forEach(([id, dataset]) => {
        const card = document.createElement("div");
        card.className = `card permission-card dataset-card ${expandedDatasetIds.has(id) ? "" : "collapsed"}`;
        card.innerHTML = `
          <div class="card-head">
            <button type="button" class="card-toggle">
              <span class="card-title"></span>
              <div class="summary-line dataset-summary"></div>
            </button>
            <span class="permission-badge">权限配置</span>
          </div>
          <div class="dataset-body">
            <div class="grid">
              <label><span>roles</span><div class="dataset-roles"></div></label>
              <label><span>description</span><input class="dataset-description" /></label>
            </div>
            <div class="matrix-actions">
              <input class="field-search" placeholder="搜索字段" />
              <div class="quick-copy-list"></div>
            </div>
            <div class="matrix-actions">
              <select class="bulk-role"></select>
              <button type="button" class="select-visible-fields">全选当前字段</button>
              <button type="button" class="clear-visible-fields">清空当前字段</button>
            </div>
            <div class="columns"></div>
            <div class="row-policy-editor"></div>
          </div>
        `;
        card.dataset.datasetId = id;
        card.querySelector(".card-title").textContent = id;
        card.querySelector(".dataset-summary").textContent = datasetSummary(dataset);
        card.querySelector(".card-toggle").addEventListener("click", () => toggleDatasetCard(card));
        renderRoleDropdown(card.querySelector(".dataset-roles"), dataset.roles || [], () => {
          syncDatasetsFromForm();
          renderDatasets();
          renderYaml();
        });
        card.querySelector(".dataset-description").value = dataset.description || "";
        renderFieldPermissionMatrix(card, id, dataset);
        renderRowPolicyEditor(card, id, dataset);
        wrap.appendChild(card);
      });
    }

    function datasetSummary(dataset) {
      const roles = datasetRoles(dataset).length;
      const fields = datasetFields(dataset).length;
      const path = dataset.path || "";
      const rowPolicy = dataset.row_policy?.field ? "row_policy 已启用" : "row_policy 未启用";
      return `${path} · ${roles} roles · ${fields} fields · ${rowPolicy}`;
    }

    function toggleDatasetCard(card) {
      card.classList.toggle("collapsed");
      if (card.classList.contains("collapsed")) {
        expandedDatasetIds.delete(card.dataset.datasetId);
      } else {
        expandedDatasetIds.add(card.dataset.datasetId);
      }
    }

    function datasetRoles(dataset) {
      return Array.from(new Set([...(dataset.roles || []), ...Object.keys(dataset.columns || {})])).filter(Boolean);
    }

    function datasetFields(dataset) {
      const fields = new Set();
      Object.values(dataset.columns || {}).forEach((cols) => (cols || []).forEach((col) => fields.add(col)));
      if (dataset.row_policy?.field) fields.add(dataset.row_policy.field);
      return Array.from(fields).sort();
    }

    function renderFieldPermissionMatrix(card, datasetId, dataset) {
      const roles = datasetRoles(dataset);
      const fields = datasetFields(dataset);
      const matrixWrap = card.querySelector(".columns");
      const search = card.querySelector(".field-search");
      const bulkRole = card.querySelector(".bulk-role");
      renderQuickCopyTargets(card, datasetId, dataset, roles);
      const roleOptions = roles.map((role) => `<option value="${escapeHtml(role)}">${escapeHtml(roleLabel(role))}</option>`).join("");
      bulkRole.innerHTML = roleOptions;
      const renderRows = () => {
        const query = search.value.trim().toLowerCase();
        const visibleFields = fields.filter((field) => !query || field.toLowerCase().includes(query));
        matrixWrap.innerHTML = `
          <table class="field-permission-matrix">
            <thead><tr><th>字段</th>${roles.map((role) => `<th><button type="button" class="role-toggle" data-role="${escapeHtml(role)}">${escapeHtml(roleLabel(role))}</button></th>`).join("")}</tr></thead>
            <tbody>
              ${visibleFields.map((field) => `
                <tr data-field="${escapeHtml(field)}">
                  <td><button type="button" class="field-toggle" data-field="${escapeHtml(field)}">${escapeHtml(field)}</button></td>
                  ${roles.map((role) => {
                    const allowed = new Set(dataset.columns?.[role] || []);
                    return `<td><input type="checkbox" class="matrix-cell" data-role="${escapeHtml(role)}" data-field="${escapeHtml(field)}" ${allowed.has(field) ? "checked" : ""} /></td>`;
                  }).join("")}
                </tr>
              `).join("")}
            </tbody>
          </table>
        `;
        matrixWrap.querySelectorAll(".matrix-cell").forEach((input) => input.addEventListener("change", () => {
          syncMatrixToDataset(card, datasetId);
          renderYaml();
        }));
        matrixWrap.querySelectorAll(".field-toggle").forEach((button) => button.addEventListener("click", () => {
          toggleVisibleField(card, datasetId, button.dataset.field);
        }));
        matrixWrap.querySelectorAll(".role-toggle").forEach((button) => button.addEventListener("click", () => {
          toggleVisibleRole(card, datasetId, button.dataset.role);
        }));
      };
      search.addEventListener("input", renderRows);
      card.querySelector(".select-visible-fields").addEventListener("click", () => {
        matrixWrap.querySelectorAll(`.matrix-cell[data-role="${CSS.escape(bulkRole.value)}"]`).forEach((input) => { input.checked = true; });
        syncMatrixToDataset(card, datasetId);
        renderYaml();
      });
      card.querySelector(".clear-visible-fields").addEventListener("click", () => {
        matrixWrap.querySelectorAll(`.matrix-cell[data-role="${CSS.escape(bulkRole.value)}"]`).forEach((input) => { input.checked = false; });
        syncMatrixToDataset(card, datasetId);
        renderYaml();
      });
      renderRows();
    }

    function renderQuickCopyTargets(card, datasetId, dataset, roles) {
      const wrap = card.querySelector(".quick-copy-list");
      if (roles.length < 2) {
        wrap.innerHTML = "";
        return;
      }
      const roleOptions = roles.map((role) => `<option value="${escapeHtml(role)}">${escapeHtml(roleLabel(role))}</option>`).join("");
      wrap.innerHTML = `
        <select class="quick-copy-source" aria-label="源角色">${roleOptions}</select>
        <select class="quick-copy-target" aria-label="目标角色"></select>
        <button type="button" class="copy-role-permissions">复制权限</button>
      `;
      const source = wrap.querySelector(".quick-copy-source");
      const target = wrap.querySelector(".quick-copy-target");
      const renderTargets = () => {
        target.innerHTML = roles
          .filter((role) => role !== source.value)
          .map((role) => `<option value="${escapeHtml(role)}">${escapeHtml(roleLabel(role))}</option>`)
          .join("");
      };
      source.addEventListener("change", renderTargets);
      wrap.querySelector(".copy-role-permissions").addEventListener("click", () => {
        if (!source.value || !target.value) return;
        copyRolePermissions(card, datasetId, source.value, target.value);
      });
      renderTargets();
    }

    function copyRolePermissions(card, datasetId, sourceRole, targetRole) {
      const dataset = config.datasets?.[datasetId];
      if (!dataset || !sourceRole || !targetRole) return;
      syncMatrixToDataset(card, datasetId);
      dataset.columns ||= {};
      dataset.columns[targetRole] = [...(dataset.columns[sourceRole] || [])].sort();
      renderFieldPermissionMatrix(card, datasetId, dataset);
      renderYaml();
      setStatus(`${roleLabel(sourceRole)} 权限已复制到 ${roleLabel(targetRole)}`, "ok");
    }

    function toggleVisibleField(card, datasetId, field) {
      const cells = Array.from(card.querySelectorAll(`.matrix-cell[data-field="${CSS.escape(field)}"]`));
      const shouldCheck = cells.some((input) => !input.checked);
      cells.forEach((input) => { input.checked = shouldCheck; });
      syncMatrixToDataset(card, datasetId);
      renderYaml();
    }

    function toggleVisibleRole(card, datasetId, role) {
      const cells = Array.from(card.querySelectorAll(`.matrix-cell[data-role="${CSS.escape(role)}"]`));
      const shouldCheck = cells.some((input) => !input.checked);
      cells.forEach((input) => { input.checked = shouldCheck; });
      syncMatrixToDataset(card, datasetId);
      renderYaml();
    }

    function renderRowPolicyEditor(card, datasetId, dataset) {
      const wrap = card.querySelector(".row-policy-editor");
      const fields = datasetFields(dataset);
      const attributeSources = knownAttributeKeys().map((key) => `attributes.${key}`);
      const selectedField = dataset.row_policy?.field || "";
      const selectedSource = dataset.row_policy?.source || "";
      wrap.innerHTML = `
        <div class="muted" style="margin-bottom:8px">行权限规则</div>
        <div class="grid">
          <label><span>数据字段</span><select class="row-policy-field"><option value="">不启用</option>${fields.map((field) => `<option value="${escapeHtml(field)}" ${field === selectedField ? "selected" : ""}>${escapeHtml(field)}</option>`).join("")}</select></label>
          <label><span>用户属性</span><input class="row-policy-source" value="${escapeHtml(selectedSource || attributeSources[0] || "")}" placeholder="attributes.regions" /></label>
        </div>
      `;
      wrap.querySelectorAll("select,input").forEach((input) => input.addEventListener("input", () => {
        syncRowPolicyFromEditor(card, datasetId);
        renderYaml();
      }));
    }

    function syncMatrixToDataset(card, datasetId) {
      const dataset = config.datasets?.[datasetId];
      if (!dataset) return;
      dataset.columns = {};
      card.querySelectorAll(".matrix-cell").forEach((input) => {
        dataset.columns[input.dataset.role] ||= [];
        if (input.checked && !dataset.columns[input.dataset.role].includes(input.dataset.field)) {
          dataset.columns[input.dataset.role].push(input.dataset.field);
        }
      });
      Object.keys(dataset.columns).forEach((role) => dataset.columns[role].sort());
    }

    function syncRowPolicyFromEditor(card, datasetId) {
      const dataset = config.datasets?.[datasetId];
      if (!dataset) return;
      const field = card.querySelector(".row-policy-field").value;
      const source = card.querySelector(".row-policy-source").value.trim();
      if (field && source) dataset.row_policy = { field, source };
      else delete dataset.row_policy;
    }

    async function discoverDatasets() {
      if (!token()) { setStatus("请输入 admin token", "err"); return; }
      setStatus("扫描中...");
      try {
        const res = await fetch("/admin/config/discover-datasets", { headers: authHeaders() });
        const body = await readJsonResponse(res);
        if (!res.ok) { setStatus(body.error?.message || "扫描失败", "err"); return; }
        renderDiscoveredDatasets(body.datasets || []);
        setStatus(`发现 ${(body.datasets || []).length} 张数据表`, "ok");
      } catch (err) {
        setStatus(errorMessage(err, "扫描失败"), "err");
      }
    }

    function renderDiscoveredDatasets(datasets) {
      const wrap = $("discovered-datasets");
      wrap.innerHTML = "";
      if (datasets.length) {
        const heading = document.createElement("div");
        heading.className = "section-label";
        heading.textContent = "发现的数据表 · 候选数据表清单";
        wrap.appendChild(heading);
      }
      datasets.forEach((dataset) => {
        const card = document.createElement("div");
        card.className = "card candidate-card discovered-card collapsed";
        card.innerHTML = `
          <div class="card-head">
            <button type="button" class="card-toggle">
              <span class="card-title"></span>
              <div class="summary-line discovered-summary"></div>
            </button>
            <span class="candidate-badge">候选表</span>
            <button class="add-discovered"></button>
          </div>
          <div class="discovered-body"><div class="columns"></div></div>
        `;
        card.querySelector(".card-title").textContent = dataset.id;
        card.querySelector(".discovered-summary").innerHTML = `${escapeHtml(dataset.path)} · ${dataset.file_count} files · <span class="field-count">${(dataset.columns || []).length} fields</span>`;
        card.querySelector(".card-toggle").addEventListener("click", () => toggleDiscoveredCard(card));
        const button = card.querySelector(".add-discovered");
        button.textContent = dataset.configured ? "已配置" : "添加到 YAML";
        button.disabled = Boolean(dataset.configured);
        button.addEventListener("click", () => addDiscoveredDataset(dataset));
        card.querySelector(".columns").innerHTML = (dataset.columns || []).map((col) => `<span class="pill">${escapeHtml(col)}</span>`).join("");
        wrap.appendChild(card);
      });
    }

    function toggleDiscoveredCard(card) {
      card.classList.toggle("collapsed");
    }

    function addDiscoveredDataset(dataset) {
      config.datasets ||= {};
      config.datasets[dataset.id] = {
        description: dataset.description || dataset.id,
        path: dataset.path,
        roles: DEFAULT_ROLES,
        columns: Object.fromEntries(DEFAULT_ROLES.map((role) => [role, dataset.columns || []])),
      };
      renderDatasets();
      renderYaml();
      setStatus(`${dataset.id} 已添加到 YAML`, "ok");
    }

    function syncDatasetsFromForm() {
      document.querySelectorAll("#dataset-list .card").forEach((card) => {
        const id = card.dataset.datasetId;
        if (!id || !config.datasets?.[id]) return;
        const dataset = config.datasets[id];
        dataset.description = card.querySelector(".dataset-description").value.trim();
        dataset.roles = selectedRoles(card.querySelector(".dataset-roles"));
        syncMatrixToDataset(card, id);
        syncRowPolicyFromEditor(card, id);
      });
    }

    function syncAllFromForms() {
      syncFeishuForm();
      syncUsersFromForm();
      syncDatasetsFromForm();
      syncSettingsFromForm();
    }

    function validateBeforeSave() {
      const errors = [];
      Object.entries(config.datasets || {}).forEach(([id, dataset]) => {
        const roles = dataset.roles || [];
        if (!roles.length) errors.push(`数据集 ${id} 至少需要一个角色`);
        roles.forEach((role) => {
          if (!(dataset.columns?.[role] || []).length) errors.push(`数据集 ${id} 的 ${roleLabel(role)} 至少需要一个字段`);
        });
        if (dataset.row_policy?.field && !datasetFields(dataset).includes(dataset.row_policy.field)) {
          errors.push(`数据集 ${id} 的行权限字段不存在`);
        }
      });
      (config.auth?.feishu_users || []).forEach((user) => {
        if (!(user.roles || []).length) errors.push(`用户 ${user.name || user.id || user.open_id} 至少需要一个角色`);
      });
      return errors;
    }

    function applyYamlToForm() {
      try {
        const parsed = parseSimpleYaml($("yaml").value);
        if (!parsed || typeof parsed !== "object") throw new Error("YAML 内容不是对象");
        config = parsed;
        renderAll();
        $("yaml-apply-message").textContent = "YAML 已应用到视觉表单";
        setStatus("YAML 已应用到表单", "ok");
      } catch (err) {
        $("yaml-apply-message").textContent = err.message || "YAML 解析失败";
        setStatus(errorMessage(err, "YAML 解析失败"), "err");
      }
    }

    function parseSimpleYaml(text) {
      const lines = text.split(/\r?\n/)
        .filter((line) => line.trim() && !line.trim().startsWith("#"))
        .map((line) => ({ indent: line.match(/^ */)[0].length, text: line.trim() }));
      if (!lines.length) return {};
      const [value, nextIndex] = parseYamlBlock(lines, 0, lines[0].indent);
      if (nextIndex < lines.length) throw new Error("YAML 缩进不一致，无法应用到表单");
      return value;
    }

    function parseYamlBlock(lines, index, indent) {
      if (index >= lines.length || lines[index].indent < indent) return [{}, index];
      if (lines[index].text === "-" || lines[index].text.startsWith("- ")) {
        const list = [];
        while (index < lines.length && lines[index].indent === indent && (lines[index].text === "-" || lines[index].text.startsWith("- "))) {
          const itemText = lines[index].text === "-" ? "" : lines[index].text.slice(2).trim();
          if (!itemText) {
            const [child, nextIndex] = parseYamlBlock(lines, index + 1, indent + 2);
            list.push(child);
            index = nextIndex;
          } else if (itemText.includes(":") && !itemText.startsWith('"')) {
            const [key, value] = parseYamlKeyValue(itemText);
            const item = {};
            item[key] = value === null ? {} : value;
            if (value === null) {
              const [child, nextIndex] = parseYamlBlock(lines, index + 1, indent + 2);
              item[key] = child;
              index = nextIndex;
            } else {
              index += 1;
            }
            list.push(item);
          } else {
            list.push(parseYamlScalar(itemText));
            index += 1;
          }
        }
        return [list, index];
      }
      const obj = {};
      while (index < lines.length && lines[index].indent === indent && lines[index].text !== "-" && !lines[index].text.startsWith("- ")) {
        const [key, value] = parseYamlKeyValue(lines[index].text);
        if (!key) throw new Error("YAML key 不能为空");
        if (value === null) {
          const [child, nextIndex] = parseYamlBlock(lines, index + 1, indent + 2);
          obj[key] = child;
          index = nextIndex;
        } else {
          obj[key] = value;
          index += 1;
        }
      }
      return [obj, index];
    }

    function parseYamlKeyValue(text) {
      const separator = text.indexOf(":");
      if (separator < 0) throw new Error(`YAML 行缺少冒号：${text}`);
      const key = text.slice(0, separator).trim();
      const rawValue = text.slice(separator + 1).trim();
      return [key, rawValue ? parseYamlScalar(rawValue) : null];
    }

    function parseYamlScalar(value) {
      if (value === "true") return true;
      if (value === "false") return false;
      if (/^\d+$/.test(value)) return Number(value);
      if (value.startsWith("[") && value.endsWith("]")) {
        return value.slice(1, -1).split(",").map((item) => item.trim()).filter(Boolean);
      }
      return value.replace(/^"|"$/g, "");
    }

    function renderSettings() {
      const s = config.settings || {};
      $("data-root").value = s.data_root || "";
      $("max-limit").value = s.max_limit || "";
      $("default-limit").value = s.default_limit || "";
      $("timeout").value = s.query_timeout_seconds || "";
    }

    function syncSettingsFromForm() {
      config.settings ||= {};
      config.settings.data_root = $("data-root").value.trim();
      config.settings.max_limit = Number($("max-limit").value);
      config.settings.default_limit = Number($("default-limit").value);
      config.settings.query_timeout_seconds = Number($("timeout").value);
    }

    function renderYaml() {
      $("yaml").value = dump(config);
    }

    function escapeHtml(text) {
      return String(text).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }

    function jsyamlDump(obj, indent = 0) {
      if (Array.isArray(obj)) {
        if (!obj.length) return "[]";
        return obj.map((item) => {
          const prefix = " ".repeat(indent) + "-";
          if (item && typeof item === "object") {
            const rendered = jsyamlDump(item, indent + 2);
            if (rendered === "{}" || rendered === "[]") return prefix + " " + rendered;
            return prefix + "\n" + rendered;
          }
          return prefix + " " + formatScalar(item);
        }).join("\n");
      }
      if (obj && typeof obj === "object") {
        if (!Object.keys(obj).length) return "{}";
        return Object.entries(obj).map(([key, value]) => {
          if (value && typeof value === "object") {
            const rendered = jsyamlDump(value, indent + 2);
            if (rendered === "{}" || rendered === "[]") return " ".repeat(indent) + key + ": " + rendered;
            return " ".repeat(indent) + key + ":\n" + rendered;
          }
          return " ".repeat(indent) + key + ": " + formatScalar(value);
        }).join("\n");
      }
      return formatScalar(obj);
    }

    function formatYamlValue(value, indent) {
      if (value && typeof value === "object") {
        const rendered = jsyamlDump(value, indent);
        if (rendered === "{}" || rendered === "[]") return rendered;
        return rendered.includes("\n") ? "\n" + rendered : rendered;
      }
      return formatScalar(value);
    }

    function formatScalar(value) {
      if (value === null || value === undefined) return "";
      if (typeof value === "boolean" || typeof value === "number") return String(value);
      const text = String(value);
      if (!text || /[:#\[\]{},&*?|>'"%@`]/.test(text) || /^\s|\s$/.test(text)) return JSON.stringify(text);
      return text;
    }
  </script>
</body>
</html>"""
