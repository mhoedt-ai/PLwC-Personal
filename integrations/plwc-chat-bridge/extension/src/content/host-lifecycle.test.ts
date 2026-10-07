import assert from "node:assert/strict";
import test from "node:test";

import {
  ensurePlwcHostAttached,
  keepPlwcHostAttached,
  PLWC_HOST_ID,
  readPlwcHostOwner,
} from "./host-lifecycle";

const development = {
  extensionId: "nlogfcafjdfdoknpkbehjgihpafpipdb",
  packageVersion: "1.0.1",
};

interface FakeElement {
  id: string;
  dataset: DOMStringMap;
  isConnected: boolean;
  remove(): void;
}

function fakeHost(owner = development): FakeElement {
  const host: FakeElement = {
    id: PLWC_HOST_ID,
    dataset: {
      plwcExtensionId: owner.extensionId,
      plwcExtensionVersion: owner.packageVersion,
    },
    isConnected: false,
    remove() {
      host.isConnected = false;
    },
  };
  return host;
}

function fakeDocument() {
  let activeHost: FakeElement | null = null;
  let appendCount = 0;
  const body = {
    append(host: FakeElement) {
      activeHost?.remove();
      host.isConnected = true;
      activeHost = host;
      appendCount += 1;
    },
  };
  return {
    body,
    documentElement: body,
    getElementById(id: string) {
      return activeHost?.isConnected && activeHost.id === id ? activeHost : null;
    },
    setActiveHost(host: FakeElement | null) {
      activeHost = host;
      if (host) host.isConnected = true;
    },
    get appendCount() {
      return appendCount;
    },
  };
}

function observerHarness() {
  let callback: MutationCallback | undefined;
  let disconnected = false;
  const observer = {
    disconnect() {
      disconnected = true;
    },
    observe() {},
    takeRecords: () => [],
  } as unknown as MutationObserver;
  return {
    observer,
    factory(registeredCallback: MutationCallback) {
      callback = registeredCallback;
      return observer;
    },
    notify() {
      callback?.([], observer);
    },
    get disconnected() {
      return disconnected;
    },
  };
}

test("the PLwC host is attached to the document body", () => {
  const documentValue = fakeDocument();
  const host = fakeHost();

  assert.equal(
    ensurePlwcHostAttached(documentValue as unknown as Document, host as unknown as HTMLElement, development),
    "attached",
  );
  assert.equal(documentValue.getElementById(PLWC_HOST_ID), host);
  assert.equal(documentValue.appendCount, 1);
});

test("the same PLwC host is restored after page hydration removes it", async () => {
  const documentValue = fakeDocument();
  const host = fakeHost();
  ensurePlwcHostAttached(documentValue as unknown as Document, host as unknown as HTMLElement, development);
  const harness = observerHarness();
  keepPlwcHostAttached(
    documentValue as unknown as Document,
    host as unknown as HTMLElement,
    development,
    harness.factory,
  );

  host.remove();
  harness.notify();
  harness.notify();
  await Promise.resolve();

  assert.equal(documentValue.getElementById(PLWC_HOST_ID), host);
  assert.equal(documentValue.appendCount, 2);
});

test("the observer stops when a higher-priority store extension owns the host", async () => {
  const documentValue = fakeDocument();
  const host = fakeHost();
  ensurePlwcHostAttached(documentValue as unknown as Document, host as unknown as HTMLElement, development);
  const harness = observerHarness();
  keepPlwcHostAttached(
    documentValue as unknown as Document,
    host as unknown as HTMLElement,
    development,
    harness.factory,
  );

  host.remove();
  const edgeStoreHost = fakeHost({
    extensionId: "nncomdhcalhlgkfjhkckdgooiekhoplk",
    packageVersion: "1.0.1",
  });
  documentValue.setActiveHost(edgeStoreHost);
  harness.notify();
  await Promise.resolve();

  assert.equal(readPlwcHostOwner(edgeStoreHost as unknown as HTMLElement)?.extensionId, edgeStoreHost.dataset.plwcExtensionId);
  assert.equal(documentValue.getElementById(PLWC_HOST_ID), edgeStoreHost);
  assert.equal(harness.disconnected, true);
});
