/**
 * knowledge-only-writes — path protection for the teaching agent's brain.
 *
 * Alvar's job is to teach, not build: it must read and write the knowledge
 * base (docs/, maps/, sessions/, lessons/, AGENTS.md) but never the code
 * that runs it (src/, tests/, tools/, pyproject, .env, ...). Prompt rules
 * leak (decision log 2026-10-02), so this extension makes the boundary
 * physical: every write/edit tool call is path-checked, and bash is
 * reduced to a read-only + git allowlist (bash can otherwise write any
 * path; git is needed for the session-close commit).
 *
 * This guards against ACCIDENTS (model writes code mid-lesson), not a
 * determined adversary — the model is a teacher, not an attacker.
 * Loaded via `pi --extension <this file>` by the teaching-agent runtime.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import path from "node:path";

/** Knowledge-base paths the teacher may write, relative to cwd. */
const WRITABLE_DIRS = ["docs", "maps", "sessions", "lessons", "assets", "out", "data"];
const WRITABLE_FILES = ["AGENTS.md", "README.md"];

/** bash is kept only for git commits and read-only inspection. */
const BASH_ALLOW = /^\s*(git|date|ls|grep|rg|find|cat|head|tail|wc|pwd|echo|sed\s+-n)\b/;

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    const name = event.toolName;

    if (name === "write" || name === "edit") {
      const target = path.resolve(String(event.input?.path ?? ""));
      const rel = path.relative(process.cwd(), target);
      const ok =
        WRITABLE_FILES.includes(rel) ||
        WRITABLE_DIRS.some(
          (dir) => rel === dir || rel.startsWith(dir + path.sep),
        );
      if (!ok) {
        return {
          block: true,
          reason:
            `Writes are limited to the knowledge base (${WRITABLE_DIRS.join("/, ")}/, ` +
            `${WRITABLE_FILES.join(", ")}); '${rel}' is project code or config. ` +
            "Its job is to teach, not build — describe the change in chat instead.",
        };
      }
      return undefined;
    }

    if (name === "bash") {
      const command = String(event.input?.command ?? "");
      // No redirection at all: git/date/reads never need it, and it is the
      // one bash feature that can silently write or truncate code files.
      if (/[^<]>>?|>\s*&/.test(command)) {
        return {
          block: true,
          reason:
            "Output redirection is disabled for the teacher (it can write code files). " +
            "Use the write/edit tools for knowledge-base files.",
        };
      }
      if (!BASH_ALLOW.test(command)) {
        return {
          block: true,
          reason:
            "The teacher's shell is read-only + git (git, date, ls, grep, rg, find, cat, " +
            "head, tail, wc, pwd, echo). Its job is to teach, not build.",
        };
      }
    }

    return undefined;
  });
}
