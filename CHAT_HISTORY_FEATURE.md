# Chat History Context Feature

## Overview

The AgustoGPT UI now automatically includes conversation history with each query, enabling context-aware responses and intelligent follow-up questions.

## How It Works

### Automatic Context Inclusion

When you ask a question, the system automatically includes the **last 2 messages** from your conversation:

1. **User asks**: "What are the key risks in the banking sector?"
2. **Assistant responds**: "The main risks include credit risk, liquidity risk..."
3. **User asks follow-up**: "How does this compare to 2023?"
4. **System automatically includes** the previous Q&A in the new query

**⚠️ Important**: The chat history is only sent to the API internally. **In the UI, you will only see your original query**, not the enhanced version with history prepended. This keeps the chat interface clean and readable.

### Query Format

The enhanced query sent to the agent API looks like this:

```
Chat History is: - user: What are the key risks in the banking sector?, assistant: The main risks include credit risk, liquidity risk, and operational risk.... See if the current user query relates to one of the chat history and answer accordingly. How does this compare to 2023?
```

This allows the AI to understand that "this" refers to banking sector risks and "compare to 2023" means comparing current risks to 2023.

## Features

### 1. Context-Aware Responses
- **Follow-up questions**: Ask "What about insurance?" after asking about banking
- **Comparisons**: "How does this compare to last year?"
- **Clarifications**: "Can you explain that in more detail?"
- **References**: "What were the top 3 you mentioned?"

### 2. Smart Truncation
- Long messages (>200 characters) are automatically truncated
- Ensures the context doesn't become too large
- Preserves the most important parts of the conversation

### 3. Visual Indicator
When chat history is being used, you'll see:
- 💬 "Using conversation context..." in the assistant's message

### 4. Configurable
You can enable/disable this feature in Development Mode.

## Usage Examples

### Example 1: Follow-up Questions

**Conversation:**
```
User: "What are the trends in the oil & gas industry?"
Assistant: [Detailed response about oil & gas trends]

User: "What about electricity?"
```

The system knows you're asking about trends in the electricity industry because it has the context from the previous message.

### Example 2: Comparisons

**Conversation:**
```
User: "Show me banking sector performance in 2024"
Assistant: [Banking sector 2024 data]

User: "How does this compare to 2023?"
```

The AI understands "this" refers to banking sector performance.

### Example 3: Clarifications

**Conversation:**
```
User: "What are the main challenges in telecommunications?"
Assistant: [Lists 5 challenges]

User: "Can you elaborate on the first one?"
```

The AI knows which challenge you're referring to.

## Controlling the Feature

### Enable Development Mode

Add to your `.env` file:
```bash
ENABLE_DEV_MODE=true
```

### Access Chat History Settings

1. Open the main application
2. Scroll to the bottom of the sidebar
3. Look for **"🔧 Development Mode"**
4. Expand **"Chat History Context"**

### Toggle On/Off

- ✅ **Enabled (Default)**: Includes last 2 messages for context
- ❌ **Disabled**: Each query is treated independently

### Preview Context

When enabled, the Development Mode shows a preview of what chat history will be included with your next query.

## Debug Mode

To see exactly what's being sent to the API, enable query debugging:

Add to `.env`:
```bash
DEBUG_QUERIES=true
```

This will show in the sidebar:
- 📝 The enhanced query with chat history included
- Truncated to first 150 characters for readability

## Benefits

### For Users
- ✅ More natural conversations
- ✅ No need to repeat context
- ✅ Ask follow-up questions naturally
- ✅ Get more relevant answers

### For Development
- ✅ Easy to toggle on/off for testing
- ✅ Preview what context is being sent
- ✅ Debug mode shows full queries
- ✅ Configurable number of messages (default: 2)

## Technical Details

### Implementation

```python
def get_recent_chat_history(num_messages: int = 2) -> str:
    """Get the most recent chat messages for context"""
    # Gets last N messages from session state
    # Formats as: "Chat History is: - role: content, ..."
    # Truncates long messages to 200 characters
```

### Integration

The chat history is automatically prepended to the user query before sending to the agent API:

```python
enhanced_query = chat_history + user_query
payload = {"user_query": enhanced_query, ...}
```

### Performance

- **Minimal overhead**: Only includes 2 messages
- **Smart truncation**: Prevents overly long contexts
- **Cached in session**: No additional API calls needed

## Best Practices

### When to Enable
- ✅ For conversational interfaces
- ✅ When users ask follow-up questions
- ✅ For multi-turn conversations
- ✅ When context matters

### When to Disable
- ❌ For testing individual queries
- ❌ When each query should be independent
- ❌ For debugging specific issues
- ❌ When you want fresh responses every time

## Troubleshooting

### Context not working?
1. Check if it's enabled in Development Mode
2. Make sure `ENABLE_DEV_MODE=true` is set
3. Verify you have previous messages in the conversation

### Responses seem confused?
1. Try disabling chat history temporarily
2. Start a new conversation (click "➕ New Chat")
3. Check if the context preview shows relevant information

### Want to see what's being sent?
1. Set `DEBUG_QUERIES=true` in `.env`
2. Look in the sidebar for query previews
3. Check the "Chat History Context" preview

## Future Enhancements

Potential improvements:
- Configurable number of messages (currently fixed at 2)
- Smart context selection (most relevant messages)
- Token counting to prevent context overflow
- User-selectable messages to include
- Context summary instead of full messages

## Questions?

See also:
- `README.md` - General application documentation
- `DEV_SETUP.md` - Development setup guide
- `QUICK_START.md` - Quick start guide

