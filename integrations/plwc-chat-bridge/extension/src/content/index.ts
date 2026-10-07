import { BridgeClient } from "./bridge-client";
import { PlwcChatRenderer } from "./chat-renderer";
import { observePlwcChainStalls } from "./chain-recovery";
import { observePlwcToolCalls } from "./tool-call-observer";
import { PlwcPanel } from "../panel/plwc-panel";
import type { PlwcHostOwner } from "./host-ownership";
import {
  ensurePlwcHostAttached,
  keepPlwcHostAttached,
  PLWC_HOST_ID,
} from "./host-lifecycle";

const ALLOWED_HOSTS = new Set(["chatgpt.com", "chat.openai.com"]);

const currentOwner: PlwcHostOwner = {
  extensionId: chrome.runtime.id,
  packageVersion: chrome.runtime.getManifest().version,
};
if (ALLOWED_HOSTS.has(location.hostname)) {
  const host = document.createElement("div");
  host.id = PLWC_HOST_ID;
  host.dataset.plwcExtensionId = currentOwner.extensionId;
  host.dataset.plwcExtensionVersion = currentOwner.packageVersion;
  const shadowRoot = host.attachShadow({ mode: "open" });
  if (ensurePlwcHostAttached(document, host, currentOwner) !== "yielded") {
    keepPlwcHostAttached(document, host, currentOwner);
    const chatRenderer = new PlwcChatRenderer();
    const panel = new PlwcPanel(shadowRoot, new BridgeClient(), chatRenderer);
    panel.mount();
    chatRenderer.mount();
    observePlwcToolCalls({
      onCall: (call) => panel.offerToolCall(call),
      onConflict: (conflict) => panel.offerToolCallConflict(conflict),
    });
    observePlwcChainStalls(() => panel.recoverStalledChain());
  }
}
