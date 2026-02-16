# Global Rules (VDO Content)

**Version:** 1.0.0

---

## 1. MCP Query First

```typescript
librarian__context({ action: "inject", prompt: task });
kb__search({ query: "vdo pattern" });
```

---

## 2. Python Standards

| Rule | Severity |
|------|----------|
| Type hints required | 🟠 HIGH |
| Ruff linting | 🟠 HIGH |
| No debug prints | 🟡 MEDIUM |

---

## 3. Scene Duration

**Maximum: 8 seconds** per scene (Veo 3 limit)

---

## 4. API Keys

- Store in `.env`
- Never commit to git
- Use `os.getenv()`

---

**Status:** Active
