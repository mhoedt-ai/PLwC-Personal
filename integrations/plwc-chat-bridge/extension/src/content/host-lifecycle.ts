import { shouldClaimPlwcHost, type PlwcHostOwner } from "./host-ownership";

export const PLWC_HOST_ID = "plwc-chat-bridge-host";

export type PlwcHostAttachmentResult = "attached" | "kept" | "replaced" | "yielded";

type PlwcHostDocument = Pick<Document, "body" | "documentElement" | "getElementById">;
type ObserverFactory = (callback: MutationCallback) => MutationObserver;

export function readPlwcHostOwner(host: HTMLElement | null): PlwcHostOwner | null {
  if (!host?.dataset.plwcExtensionId) return null;
  return {
    extensionId: host.dataset.plwcExtensionId,
    packageVersion: host.dataset.plwcExtensionVersion ?? "unknown",
  };
}

export function ensurePlwcHostAttached(
  documentValue: PlwcHostDocument,
  host: HTMLElement,
  currentOwner: PlwcHostOwner,
): PlwcHostAttachmentResult {
  const existingHost = documentValue.getElementById(PLWC_HOST_ID);
  if (existingHost === host && host.isConnected) return "kept";

  if (existingHost && !shouldClaimPlwcHost(currentOwner, readPlwcHostOwner(existingHost))) {
    return "yielded";
  }

  existingHost?.remove();
  (documentValue.body ?? documentValue.documentElement).append(host);
  return existingHost ? "replaced" : "attached";
}

export function keepPlwcHostAttached(
  documentValue: Document,
  host: HTMLElement,
  currentOwner: PlwcHostOwner,
  createObserver: ObserverFactory = (callback) => new MutationObserver(callback),
): MutationObserver {
  let scheduled = false;
  let observer: MutationObserver;

  const restore = () => {
    scheduled = false;
    if (documentValue.getElementById(PLWC_HOST_ID) === host && host.isConnected) return;
    if (ensurePlwcHostAttached(documentValue, host, currentOwner) === "yielded") {
      observer.disconnect();
    }
  };

  observer = createObserver(() => {
    if (documentValue.getElementById(PLWC_HOST_ID) === host && host.isConnected) return;
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(restore);
  });
  observer.observe(documentValue, { childList: true, subtree: true });
  return observer;
}
