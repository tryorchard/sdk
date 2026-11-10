/** Errors thrown by the Orchard SDK. @packageDocumentation */

/** Base class for every error the SDK throws. */
export class OrchardError extends Error {}

/** A non-2xx REST response. */
export class ApiError extends OrchardError {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(ApiError.message(status, detail));
    this.name = "ApiError";
  }

  private static message(status: number, detail: string): string {
    if (status === 401) return "the API key is invalid or expired (check ORCHARD_API_KEY)";
    if (status === 403) return detail || "forbidden";
    if (status === 404) return detail || "no such sandbox, or this key may not reach it";
    return detail || `request failed (${status})`;
  }
}

/** A sandbox selector matched zero or more than one sandbox. */
export class SelectorError extends OrchardError {
  constructor(message: string) {
    super(message);
    this.name = "SelectorError";
  }
}

/** A WebSocket channel closed with an Orchard error code (4401/4403/4404/4502). */
export class ChannelClosedError extends OrchardError {
  constructor(
    readonly code: number,
    readonly reason = "",
  ) {
    super(`channel closed (${code})${reason ? `: ${reason}` : ""}`);
    this.name = "ChannelClosedError";
  }
}
