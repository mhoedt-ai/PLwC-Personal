export type ChatTurnRole = "assistant" | "user";

const TURN_SELECTOR = "[data-turn]";
const MESSAGE_SELECTOR = "[data-message-author-role]";
const CONTENT_SEARCH_UNIT_SELECTOR = "[data-content-search-unit-key]";
const CHATGPT_SEARCH_UNIT_SELECTOR = "[data-chatgpt-search-unit-key]";
const ASSISTANT_MARKDOWN_SELECTOR = '[data-markdown-text-style="assistant-message"]';
const USER_MARKDOWN_SELECTOR = '[data-markdown-text-tone="user-message"]';
const USER_BUBBLE_SELECTOR = '[data-user-message-bubble="true"]';

export const CHAT_TURN_SELECTOR = [
  TURN_SELECTOR,
  MESSAGE_SELECTOR,
  CONTENT_SEARCH_UNIT_SELECTOR,
  CHATGPT_SEARCH_UNIT_SELECTOR,
  ASSISTANT_MARKDOWN_SELECTOR,
  USER_MARKDOWN_SELECTOR,
  USER_BUBBLE_SELECTOR,
].join(", ");

function parseChatTurnRole(value: string | null): ChatTurnRole | null {
  return value === "assistant" || value === "user" ? value : null;
}

function parseSearchUnitRole(value: string | null): ChatTurnRole | null {
  return parseChatTurnRole(value?.match(/:(assistant|user)$/u)?.[1] ?? null);
}

function collectResolvedRoles(element: Element): Set<ChatTurnRole> {
  const roles = new Set<ChatTurnRole>();
  const add = (role: ChatTurnRole | null): void => {
    if (role !== null) roles.add(role);
  };

  add(parseChatTurnRole(element.closest<HTMLElement>(TURN_SELECTOR)?.getAttribute("data-turn") ?? null));
  add(parseChatTurnRole(
    element.closest<HTMLElement>(MESSAGE_SELECTOR)?.getAttribute("data-message-author-role") ?? null,
  ));
  add(parseSearchUnitRole(
    element.closest<HTMLElement>(CONTENT_SEARCH_UNIT_SELECTOR)?.getAttribute("data-content-search-unit-key") ?? null,
  ));
  add(parseSearchUnitRole(
    element.closest<HTMLElement>(CHATGPT_SEARCH_UNIT_SELECTOR)?.getAttribute("data-chatgpt-search-unit-key") ?? null,
  ));
  if (element.closest<HTMLElement>(ASSISTANT_MARKDOWN_SELECTOR)) add("assistant");
  if (
    element.closest<HTMLElement>(USER_MARKDOWN_SELECTOR) ||
    element.closest<HTMLElement>(USER_BUBBLE_SELECTOR)
  ) add("user");
  return roles;
}

export function resolveChatTurnRole(element: Element): ChatTurnRole | null {
  const roles = collectResolvedRoles(element);
  return roles.size === 1 ? [...roles][0] ?? null : null;
}

export function closestChatTurnContainer(element: Element): HTMLElement | null {
  const role = resolveChatTurnRole(element);
  if (role === null) return null;

  const turn = element.closest<HTMLElement>(TURN_SELECTOR);
  if (parseChatTurnRole(turn?.getAttribute("data-turn") ?? null) === role) return turn;

  const message = element.closest<HTMLElement>(MESSAGE_SELECTOR);
  if (parseChatTurnRole(message?.getAttribute("data-message-author-role") ?? null) === role) {
    return message;
  }

  for (const selector of [CONTENT_SEARCH_UNIT_SELECTOR, CHATGPT_SEARCH_UNIT_SELECTOR]) {
    const searchUnit = element.closest<HTMLElement>(selector);
    const attribute = selector === CONTENT_SEARCH_UNIT_SELECTOR
      ? "data-content-search-unit-key"
      : "data-chatgpt-search-unit-key";
    if (parseSearchUnitRole(searchUnit?.getAttribute(attribute) ?? null) === role) return searchUnit;
  }

  const modernMarker = role === "assistant"
    ? element.closest<HTMLElement>(ASSISTANT_MARKDOWN_SELECTOR)
    : element.closest<HTMLElement>(USER_MARKDOWN_SELECTOR) ??
      element.closest<HTMLElement>(USER_BUBBLE_SELECTOR);
  return modernMarker && resolveChatTurnRole(modernMarker) === role ? modernMarker : null;
}

export function collectChatTurnContainers(
  documentValue: Document,
  role: ChatTurnRole,
): HTMLElement[] {
  const candidates = documentValue.querySelectorAll<HTMLElement>(CHAT_TURN_SELECTOR);
  const containers: HTMLElement[] = [];
  const seen = new Set<HTMLElement>();
  for (const candidate of candidates) {
    const container = closestChatTurnContainer(candidate);
    if (container === null || resolveChatTurnRole(container) !== role || seen.has(container)) continue;
    seen.add(container);
    containers.push(container);
  }
  return containers;
}

export function isChatTurnBoundary(element: Element): boolean {
  return parseChatTurnRole(element.getAttribute("data-turn")) !== null ||
    parseChatTurnRole(element.getAttribute("data-message-author-role")) !== null ||
    parseSearchUnitRole(element.getAttribute("data-content-search-unit-key")) !== null ||
    parseSearchUnitRole(element.getAttribute("data-chatgpt-search-unit-key")) !== null ||
    element.getAttribute("data-markdown-text-style") === "assistant-message" ||
    element.getAttribute("data-markdown-text-tone") === "user-message" ||
    element.getAttribute("data-user-message-bubble") === "true";
}

export function chatTurnIdentity(container: HTMLElement, fallbackIndex: number): string {
  return container.getAttribute("data-turn-id") ??
    container.getAttribute("data-message-id") ??
    container.getAttribute("data-chatgpt-selection-message-id") ??
    container.getAttribute("data-content-search-unit-key") ??
    container.getAttribute("data-chatgpt-search-unit-key") ??
    container.getAttribute("data-turn-key") ??
    container.getAttribute("data-testid") ??
    String(fallbackIndex);
}
