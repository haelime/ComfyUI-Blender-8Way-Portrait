import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
  name: "haelime.Blender8Way.ModelPicker",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "NativeModel3DInput") return;

    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      originalCreated?.apply(this, arguments);
      const pathWidget = this.widgets?.find((widget) => widget.name === "model_path");
      if (!pathWidget) return;

      this.addWidget("button", "choose_model", "Choose 3D Model…", async () => {
        const response = await api.fetchApi("/blender-8way/pick-model", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initial_path: pathWidget.value || "" }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          alert(payload.error || `Native model picker failed (HTTP ${response.status}).`);
          return;
        }
        if (!payload.cancelled && payload.path) {
          pathWidget.value = payload.path;
          app.graph.setDirtyCanvas(true, true);
        }
      });
      this.setSize([Math.max(this.size[0], 430), Math.max(this.size[1], 120)]);
    };
  },
});
