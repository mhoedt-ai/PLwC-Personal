import assert from "node:assert/strict";
import test from "node:test";

import {
  activateChatGptSendButton,
  attachToolResultImagesToChatGptComposer,
  confirmChatGptComposerInsertion,
  findChatGptComposer,
  findChatGptComposerSurface,
  imageBytesMatchMimeType,
  imagesPrecedeText,
  isChatGptSendButtonCandidate,
  lockChatGptComposerElement,
  submitInsertedChatGptComposer,
  unlockChatGptComposerElement,
  waitForChatGptResultInsertionReadiness,
} from "./composer";

type Rect = Pick<DOMRect, "bottom" | "height" | "left" | "right" | "top" | "width">;

class TestHTMLElement {
  accept = "";
  readonly children: TestHTMLElement[] = [];
  disabled = false;
  parentElement: TestHTMLElement | null = null;
  textContent = "";
  value = "";
  files: FileList | null = null;
  readonly dispatchedEvents: string[] = [];

  constructor(
    readonly tagName: string,
    private readonly attributes = new Map<string, string>(),
  ) {}

  get isContentEditable(): boolean {
    const value = this.getAttribute("contenteditable");
    return value !== null && value.toLowerCase() !== "false";
  }

  append(child: TestHTMLElement): void {
    child.parentElement = this;
    this.children.push(child);
  }

  blur(): void {}

  dispatchEvent(event: Event): boolean {
    this.dispatchedEvents.push(event.type);
    return true;
  }

  closest(selector: string): TestHTMLElement | null {
    let current: TestHTMLElement | null = this;
    while (current) {
      if (selector === "[data-message-author-role]" && current.getAttribute("data-message-author-role") !== null) {
        return current;
      }
      if (selector === "form" && current.tagName === "FORM") return current;
      current = current.parentElement;
    }
    return null;
  }

  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }

  querySelector(selector: string): TestHTMLElement | null {
    return this.querySelectorAll(selector)[0] ?? null;
  }

  querySelectorAll(selector: string): TestHTMLElement[] {
    return this.children.flatMap((child) => [
      ...(child.matches(selector) ? [child] : []),
      ...child.querySelectorAll(selector),
    ]);
  }

  matches(selector: string): boolean {
    if (selector === "textarea") return this.tagName === "TEXTAREA";
    if (selector === "input") return this.tagName === "INPUT";
    if (selector === "input[type='file']") {
      return this.tagName === "INPUT" && this.getAttribute("type") === "file";
    }
    if (selector === "#prompt-textarea") return this.getAttribute("id") === "prompt-textarea";
    if (selector === "[data-testid='composer-input']") return this.getAttribute("data-testid") === "composer-input";
    if (selector === "[data-testid='composer']") return this.getAttribute("data-testid") === "composer";
    if (selector === "[data-lexical-editor='true']") return this.getAttribute("data-lexical-editor") === "true";
    if (selector === "[role='textbox']") return this.getAttribute("role") === "textbox";
    if (selector.includes("[contenteditable]")) {
      const value = this.getAttribute("contenteditable");
      return value !== null && value.toLowerCase() !== "false";
    }
    if (selector.startsWith("form ")) return false;
    return false;
  }
}

Object.defineProperty(globalThis, "HTMLElement", {
  configurable: true,
  value: TestHTMLElement,
});

function testDocument(root: TestHTMLElement): Document {
  return {
    defaultView: {
      getComputedStyle: () => ({ display: "block", visibility: "visible" }) as CSSStyleDeclaration,
    },
    querySelectorAll: (selector: string) => [
      ...(root.matches(selector) ? [root] : []),
      ...root.querySelectorAll(selector),
    ],
  } as unknown as Document;
}

function mockElement(rect: Rect, parentElement: HTMLElement | null = null): HTMLElement {
  return {
    getBoundingClientRect: () => rect as DOMRect,
    parentElement,
  } as unknown as HTMLElement;
}

test("uses the rounded composer shell for vertical launcher alignment", () => {
  const outer = mockElement({ bottom: 980, height: 80, left: 600, right: 1_500, top: 900, width: 900 });
  const shell = mockElement(
    { bottom: 965.6, height: 52, left: 666, right: 1_434, top: 913.6, width: 768 },
    outer,
  );
  const editorRow = mockElement(
    { bottom: 969, height: 59, left: 710, right: 1_257, top: 910, width: 547 },
    shell,
  );
  const composer = mockElement(
    { bottom: 968, height: 42, left: 717, right: 1_251, top: 926, width: 534 },
    editorRow,
  );
  const radii = new Map<HTMLElement, string>([
    [outer, "28px"],
    [shell, "28px"],
  ]);
  const documentValue = {
    defaultView: {
      getComputedStyle: (element: HTMLElement) => {
        const radius = radii.get(element) ?? "0px";
        return {
          borderBottomLeftRadius: radius,
          borderBottomRightRadius: radius,
          borderTopLeftRadius: radius,
          borderTopRightRadius: radius,
        } as CSSStyleDeclaration;
      },
    },
  } as unknown as Document;

  assert.equal(findChatGptComposerSurface(composer, documentValue), shell);
});

test("resolves a nested editable composer inside the current prompt container", () => {
  const container = new TestHTMLElement("DIV", new Map([["id", "prompt-textarea"]]));
  const editor = new TestHTMLElement("DIV", new Map([
    ["contenteditable", "plaintext-only"],
    ["role", "textbox"],
  ]));
  container.append(editor);

  assert.equal(findChatGptComposer(testDocument(container)), editor);
});

test("does not use editable content inside previous chat messages as the composer", () => {
  const root = new TestHTMLElement("MAIN");
  const previousUserMessage = new TestHTMLElement("DIV", new Map([["data-message-author-role", "user"]]));
  const oldEditor = new TestHTMLElement("DIV", new Map([["contenteditable", "true"]]));
  const currentComposer = new TestHTMLElement("DIV", new Map([
    ["contenteditable", "plaintext-only"],
    ["role", "textbox"],
  ]));
  previousUserMessage.append(oldEditor);
  root.append(previousUserMessage);
  root.append(currentComposer);

  assert.equal(findChatGptComposer(testDocument(root)), currentComposer);
});

test("recognizes the supported image file signatures", () => {
  assert.equal(imageBytesMatchMimeType(
    Uint8Array.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    "image/png",
  ), true);
  assert.equal(imageBytesMatchMimeType(Uint8Array.from([0xff, 0xd8, 0xff]), "image/jpeg"), true);
  assert.equal(imageBytesMatchMimeType(Uint8Array.from([0xff, 0xd8, 0xff]), "image/png"), false);
});

test("retains MCP text and image ordering when choosing the composer insertion sequence", () => {
  assert.equal(imagesPrecedeText(["text", "image"]), false);
  assert.equal(imagesPrecedeText(["image", "text"]), true);
  assert.equal(imagesPrecedeText(["image"]), true);
  assert.equal(imagesPrecedeText(["text"]), false);
});

test("puts an MCP image into ChatGPT's file input instead of the text composer", () => {
  const root = new TestHTMLElement("FORM");
  const composer = new TestHTMLElement("DIV", new Map([
    ["contenteditable", "plaintext-only"],
    ["role", "textbox"],
  ]));
  const input = new TestHTMLElement("INPUT", new Map([["type", "file"]]));
  input.accept = "image/*";
  root.append(composer);
  root.append(input);
  const files: File[] = [];
  class FakeFile {
    constructor(
      readonly parts: BlobPart[],
      readonly name: string,
      readonly options: FilePropertyBag,
    ) {}
  }
  class FakeDataTransfer {
    readonly items = { add: (file: File) => { files.push(file); } };
    get files(): FileList {
      return files as unknown as FileList;
    }
  }
  class FakeEvent {
    constructor(readonly type: string) {}
  }
  const documentValue = testDocument(root);
  Object.assign(documentValue.defaultView!, {
    DataTransfer: FakeDataTransfer,
    Event: FakeEvent,
    File: FakeFile,
    atob: globalThis.atob,
  });
  const data = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).toString("base64");

  const result = attachToolResultImagesToChatGptComposer([{
    byteLength: 8,
    contentIndex: 1,
    data,
    fileName: "page.png",
    mimeType: "image/png",
    type: "image",
  }], composer as unknown as HTMLElement, documentValue);

  assert.equal(result, "attached");
  assert.equal(files.length, 1);
  assert.equal((files[0] as unknown as FakeFile).name, "page.png");
  assert.deepEqual(input.dispatchedEvents, ["input", "change"]);
  assert.equal(composer.textContent, "");
});

function mockButton(label: string | null): HTMLButtonElement {
  return {
    getAttribute: (name: string) => name === "aria-label" ? label : null,
    textContent: "",
  } as unknown as HTMLButtonElement;
}

test("accepts the current localized composer submit control", () => {
  assert.equal(isChatGptSendButtonCandidate(mockButton("Nachricht übermitteln")), true);
  assert.equal(isChatGptSendButtonCandidate(mockButton("Send message")), true);
});

test("does not mistake the shared composer voice control for submit", () => {
  assert.equal(isChatGptSendButtonCandidate(mockButton("Voice starten")), false);
  assert.equal(isChatGptSendButtonCandidate(mockButton("Diktat starten")), false);
  assert.equal(isChatGptSendButtonCandidate(mockButton("Antwortgenerierung beenden")), false);
});

test("submits through the owning ChatGPT form with the active button", () => {
  let requestedWith: HTMLButtonElement | null = null;
  let clicks = 0;
  const form = {
    requestSubmit: (button: HTMLButtonElement) => {
      requestedWith = button;
    },
  } as unknown as HTMLFormElement;
  const send = {
    click: () => { clicks += 1; },
    closest: () => form,
    form,
    type: "submit",
  } as unknown as HTMLButtonElement;

  assert.equal(activateChatGptSendButton(send), "form");
  assert.equal(requestedWith, send);
  assert.equal(clicks, 0);
});

test("falls back to a direct click outside a submit form", () => {
  let clicks = 0;
  const send = {
    click: () => { clicks += 1; },
    closest: () => null,
    form: null,
    type: "button",
  } as unknown as HTMLButtonElement;

  assert.equal(activateChatGptSendButton(send), "click");
  assert.equal(clicks, 1);
});

test("retries a rejected native submit with a direct click", async () => {
  let composerEmpty = false;
  let nativeSubmits = 0;
  let clicks = 0;
  const form = {
    requestSubmit: () => { nativeSubmits += 1; },
  } as unknown as HTMLFormElement;
  const send = {
    click: () => {
      clicks += 1;
      composerEmpty = true;
    },
    closest: () => form,
    form,
    type: "submit",
  } as unknown as HTMLButtonElement;

  const result = await submitInsertedChatGptComposer(
    {
      findSendButton: () => send,
      isComposerEmpty: () => composerEmpty,
      wait: async () => undefined,
    },
    { confirmationAttempts: 1, maxSubmitAttempts: 2, pollIntervalMs: 0 },
  );

  assert.equal(result, "submitted");
  assert.equal(nativeSubmits, 1);
  assert.equal(clicks, 1);
});

test("reports a missing submit control only after the configured wait", async () => {
  let waits = 0;
  const result = await submitInsertedChatGptComposer(
    {
      findSendButton: () => null,
      isComposerEmpty: () => false,
      wait: async () => { waits += 1; },
    },
    { pollIntervalMs: 0, sendButtonWaitAttempts: 3 },
  );

  assert.equal(result, "send-button-not-found");
  assert.equal(waits, 3);
});

test("does not report success when the controlled editor clears before a send attempt", async () => {
  let sendLookups = 0;
  const result = await submitInsertedChatGptComposer(
    {
      findSendButton: () => {
        sendLookups += 1;
        return null;
      },
      isComposerEmpty: () => true,
      wait: async () => undefined,
    },
    { pollIntervalMs: 0, sendButtonWaitAttempts: 3 },
  );

  assert.equal(result, "composer-rejected-insertion");
  assert.equal(sendLookups, 0);
});

test("detects focus reconciliation that removes a visible controlled-editor insertion", async () => {
  let composerText = "# PLwC Tool Result";
  let focusCycles = 0;
  const accepted = await confirmChatGptComposerInsertion(
    {
      hasExpectedText: () => composerText === "# PLwC Tool Result",
      refocus: () => {
        focusCycles += 1;
        composerText = "";
      },
      wait: async () => undefined,
    },
    { insertionConfirmationAttempts: 2, pollIntervalMs: 0 },
  );

  assert.equal(accepted, false);
  assert.equal(focusCycles, 1);
});

test("waits for ChatGPT to finish responding before inserting a result", async () => {
  let waits = 0;
  const result = await waitForChatGptResultInsertionReadiness(
    {
      isChatBusy: () => waits < 2,
      isComposerEmpty: () => true,
      wait: async () => { waits += 1; },
    },
    { pollIntervalMs: 0, readinessWaitAttempts: 5 },
  );

  assert.equal(result, "submitted");
  assert.equal(waits, 2);
});

test("does not insert a result when ChatGPT stays busy", async () => {
  let waits = 0;
  const result = await waitForChatGptResultInsertionReadiness(
    {
      isChatBusy: () => true,
      isComposerEmpty: () => true,
      wait: async () => { waits += 1; },
    },
    { pollIntervalMs: 0, readinessWaitAttempts: 3 },
  );

  assert.equal(result, "chat-not-ready");
  assert.equal(waits, 3);
});

function mockComposer(tagName: "DIV" | "TEXTAREA", contentEditable: string | null) {
  const attributes = new Map<string, string>();
  if (contentEditable !== null) attributes.set("contenteditable", contentEditable);
  let blurCalls = 0;
  const composer = {
    disabled: false,
    tagName,
    blur: () => { blurCalls += 1; },
    getAttribute: (name: string) => attributes.get(name) ?? null,
    removeAttribute: (name: string) => { attributes.delete(name); },
    setAttribute: (name: string, value: string) => { attributes.set(name, value); },
  } as unknown as HTMLElement;
  return { attributes, composer, blurCalls: () => blurCalls };
}

test("locks and restores a contenteditable ChatGPT composer", () => {
  const mocked = mockComposer("DIV", "true");

  const lock = lockChatGptComposerElement(mocked.composer);

  assert.equal(mocked.attributes.get("contenteditable"), "false");
  assert.equal(mocked.attributes.get("aria-disabled"), "true");
  assert.equal(mocked.blurCalls(), 1);
  unlockChatGptComposerElement(lock);
  assert.equal(mocked.attributes.get("contenteditable"), "true");
  assert.equal(mocked.attributes.has("aria-disabled"), false);
});

test("locks and restores a textarea ChatGPT composer", () => {
  const mocked = mockComposer("TEXTAREA", null);
  const composer = mocked.composer as HTMLTextAreaElement;

  const lock = lockChatGptComposerElement(composer);

  assert.equal(composer.disabled, true);
  unlockChatGptComposerElement(lock);
  assert.equal(composer.disabled, false);
});
