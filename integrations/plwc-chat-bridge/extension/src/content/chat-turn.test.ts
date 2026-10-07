import assert from "node:assert/strict";
import test from "node:test";

import {
  chatTurnIdentity,
  closestChatTurnContainer,
  collectChatTurnContainers,
  isChatTurnBoundary,
  resolveChatTurnRole,
} from "./chat-turn";

class TestElement {
  readonly children: TestElement[] = [];
  parentElement: TestElement | null = null;

  constructor(private readonly attributes = new Map<string, string>()) {}

  append(child: TestElement): void {
    child.parentElement = this;
    this.children.push(child);
  }

  closest(selector: string): TestElement | null {
    let current: TestElement | null = this;
    while (current) {
      const presence = selector.match(/^\[([^=\]]+)\]$/u);
      const exact = selector.match(/^\[([^=\]]+)=["']([^"']+)["']\]$/u);
      if (presence && current.getAttribute(presence[1] ?? "") !== null) return current;
      if (exact && current.getAttribute(exact[1] ?? "") === exact[2]) return current;
      current = current.parentElement;
    }
    return null;
  }

  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }
}

function asElement(value: TestElement): Element {
  return value as unknown as Element;
}

function asHtmlElement(value: TestElement): HTMLElement {
  return value as unknown as HTMLElement;
}

test("resolves content from the current outer ChatGPT turn", () => {
  const turn = new TestElement(new Map([
    ["data-turn", "assistant"],
    ["data-turn-id", "request-live-1"],
    ["data-testid", "conversation-turn-88"],
  ]));
  const roleMarker = new TestElement(new Map([["data-message-author-role", "assistant"]]));
  const renderedContent = new TestElement();
  turn.append(roleMarker);
  turn.append(renderedContent);

  assert.equal(resolveChatTurnRole(asElement(renderedContent)), "assistant");
  assert.equal(closestChatTurnContainer(asElement(renderedContent)), asHtmlElement(turn));
  assert.equal(chatTurnIdentity(asHtmlElement(turn), 0), "request-live-1");
  assert.equal(isChatTurnBoundary(asElement(turn)), true);
});

test("fails closed when nested and outer ChatGPT roles disagree", () => {
  const turn = new TestElement(new Map([["data-turn", "assistant"]]));
  const conflictingMessage = new TestElement(new Map([["data-message-author-role", "user"]]));
  const code = new TestElement();
  turn.append(conflictingMessage);
  conflictingMessage.append(code);

  assert.equal(resolveChatTurnRole(asElement(code)), null);
  assert.equal(closestChatTurnContainer(asElement(code)), null);
});

test("collects each current or legacy turn exactly once", () => {
  const currentTurn = new TestElement(new Map([["data-turn", "assistant"]]));
  const currentMarker = new TestElement(new Map([["data-message-author-role", "assistant"]]));
  currentTurn.append(currentMarker);
  const legacyMessage = new TestElement(new Map([["data-message-author-role", "assistant"]]));
  const candidates = [currentTurn, currentMarker, legacyMessage];
  const documentValue = {
    querySelectorAll: () => candidates,
  } as unknown as Document;

  assert.deepEqual(
    collectChatTurnContainers(documentValue, "assistant"),
    [asHtmlElement(currentTurn), asHtmlElement(legacyMessage)],
  );
});

test("resolves the current ChatGPT search-unit role markers", () => {
  const turn = new TestElement(new Map([["data-turn-key", "turn-current-1"]]));
  const assistantUnit = new TestElement(new Map([
    ["data-content-search-unit-key", "fallback-turn-7:2:assistant"],
    ["data-chatgpt-search-unit-key", "fallback-turn-7:2:assistant"],
  ]));
  const markdown = new TestElement(new Map([
    ["data-markdown-text-style", "assistant-message"],
  ]));
  const code = new TestElement();
  turn.append(assistantUnit);
  assistantUnit.append(markdown);
  markdown.append(code);

  assert.equal(resolveChatTurnRole(asElement(code)), "assistant");
  assert.equal(closestChatTurnContainer(asElement(code)), asHtmlElement(assistantUnit));
  assert.equal(chatTurnIdentity(asHtmlElement(assistantUnit), 0), "fallback-turn-7:2:assistant");
  assert.equal(isChatTurnBoundary(asElement(assistantUnit)), true);
});

test("collects a modern ChatGPT assistant turn only once", () => {
  const assistantUnit = new TestElement(new Map([
    ["data-content-search-unit-key", "fallback-turn-8:2:assistant"],
  ]));
  const markdown = new TestElement(new Map([
    ["data-markdown-text-style", "assistant-message"],
  ]));
  assistantUnit.append(markdown);
  const documentValue = {
    querySelectorAll: () => [assistantUnit, markdown],
  } as unknown as Document;

  assert.deepEqual(
    collectChatTurnContainers(documentValue, "assistant"),
    [asHtmlElement(assistantUnit)],
  );
});

test("distinguishes the current ChatGPT user message markers", () => {
  const userUnit = new TestElement(new Map([
    ["data-content-search-unit-key", "fallback-turn-7:0:user"],
  ]));
  const bubble = new TestElement(new Map([["data-user-message-bubble", "true"]]));
  const markdown = new TestElement(new Map([["data-markdown-text-tone", "user-message"]]));
  const text = new TestElement();
  userUnit.append(bubble);
  bubble.append(markdown);
  markdown.append(text);

  assert.equal(resolveChatTurnRole(asElement(text)), "user");
  assert.equal(closestChatTurnContainer(asElement(text)), asHtmlElement(userUnit));
  assert.equal(isChatTurnBoundary(asElement(markdown)), true);
});
