# Recommended Queries Feature

## Overview

The AgustoGPT UI now displays AI-suggested follow-up questions as interactive buttons below each response. When clicked, these buttons automatically send the recommended query with full conversation context.

## How It Works

### 1. AI Generates Recommendations

After processing your query, the AI agent returns:
- The main response
- Source citations
- **Recommended follow-up queries** (3-5 suggestions)

### 2. UI Displays as Buttons

The UI shows recommended queries as clickable buttons:

```
┌─────────────────────────────────────────────────┐
│ 🤖 Assistant Response                           │
│ The main risks in banking include...            │
│                                                  │
│ 📚 Sources from your reports:                   │
│ - 2024 Banking Industry Report                  │
│                                                  │
│ 💡 You might also want to ask:                  │
│ ┌───────────────────────────────────────────┐  │
│ │ 💬 How do these risks compare to 2023?    │  │
│ └───────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────┐  │
│ │ 💬 What mitigation strategies exist?      │  │
│ └───────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────┐  │
│ │ 💬 How does this affect insurance?        │  │
│ └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 3. One-Click Query Submission

When you click a recommended query button:
1. ✅ Query is automatically added to the chat
2. ✅ Previous response is included as context
3. ✅ API call is made with full conversation history
4. ✅ New response appears with its own recommendations

## Features

### Automatic Context Inclusion

When you click a recommended query:
- The **previous response** is automatically included in the chat history
- The AI understands the context and provides relevant answers
- No need to manually reference previous questions

### Intelligent Suggestions

The AI agent generates recommendations based on:
- Current response content
- Available reports and data
- Natural conversation flow
- User's industry access

### Seamless User Experience

- **No typing required**: Just click to ask
- **Maintains conversation flow**: Each query builds on previous ones
- **Always contextual**: Recommendations relate to current topic
- **Easy to explore**: Multiple pathways to dig deeper

## Example Conversation Flow

### Step 1: Initial Query
```
User: "What are the key trends in the oil & gas sector?"
```

**AI Response**: Discusses trends like renewable energy transition, digital transformation, etc.

**Recommended Queries Displayed:**
- 💬 How do these trends compare to the downstream sector?
- 💬 What are the investment implications?
- 💬 How is Nigeria positioned in these trends?

### Step 2: User Clicks Recommendation
```
User clicks: "How do these trends compare to the downstream sector?"
```

**What Happens:**
1. Query is automatically submitted
2. Previous response about upstream trends is included in context
3. AI provides comparative analysis

**New Recommendations:**
- 💬 What are the regulatory challenges for downstream?
- 💬 How does refining capacity affect these trends?
- 💬 What about petrochemicals?

### Step 3: Continue Exploration
The user can keep clicking recommendations to explore the topic deeply without typing.

## Technical Implementation

### API Response Structure

The agent API returns recommended queries in the response:

```json
{
  "user_query": "What are the key trends?",
  "response": "The main trends include...",
  "document_information": [...],
  "current_date": "2025-11-20",
  "recommended_queries": [
    "How do these trends compare to last year?",
    "What are the implications for investors?",
    "Which sectors are most affected?"
  ]
}
```

### UI Rendering

The UI processes recommended queries:

```python
# Extract from response
recommended_queries = response.get('recommended_queries', [])

# Display as buttons
for query in recommended_queries:
    if st.button(f"💬 {query}"):
        # Trigger query with full context
        st.session_state.recommended_query = query
        st.rerun()
```

### Context Preservation

When a recommended query is clicked:

1. **Previous messages** are already in session state
2. **Chat history context** feature automatically includes last 2 messages
3. **Enhanced query** sent to API includes full context
4. **UI displays** only the clicked recommended query (not the enhanced version)

## Benefits

### For Users

✅ **Faster exploration**: No typing required  
✅ **Discover insights**: AI suggests relevant questions you might not have thought of  
✅ **Natural flow**: Conversation builds logically  
✅ **Time-saving**: Get to insights faster  

### For Research

✅ **Comprehensive coverage**: Explore topics from multiple angles  
✅ **Follow connections**: Discover relationships between sectors  
✅ **Deep dives**: Go from overview to specific details  
✅ **Cross-referencing**: Compare different reports and timeframes  

## Best Practices

### For Users

1. **Start broad**: Begin with general questions
2. **Use recommendations**: Let the AI guide deeper exploration
3. **Mix and match**: Combine recommended queries with your own
4. **Follow threads**: Click recommendations that interest you most

### For API Developers

1. **Provide 3-5 recommendations**: Not too few, not overwhelming
2. **Make them specific**: Concrete questions work better than vague ones
3. **Vary the angles**: Cover different aspects (time, sector, impact, etc.)
4. **Consider context**: Base recommendations on what user asked and what's in the response

## Customization

### Disable Feature

If you don't want to see recommended queries, the API can return an empty list:

```python
"recommended_queries": []
```

### Styling

The buttons use Streamlit's default styling:
- `type="secondary"` for a softer appearance
- `use_container_width=True` for full-width buttons
- 💬 emoji for visual consistency

## Troubleshooting

### Buttons Not Appearing

**Possible causes:**
1. API returning empty `recommended_queries` list
2. Response not including `recommended_queries` field
3. UI error in rendering

**Solution:**
- Check API response includes `recommended_queries`
- Verify it's a list of strings
- Check browser console for errors

### Buttons Not Working

**Possible causes:**
1. Duplicate button keys
2. Session state not updating
3. Rerun not triggering

**Solution:**
- Each button has unique key based on timestamp and index
- Check session state in debug mode
- Ensure `st.rerun()` is called

### Context Not Preserved

**Possible causes:**
1. Chat history feature disabled
2. Messages not being stored properly
3. API not processing context

**Solution:**
- Verify `enable_chat_history=True`
- Check `st.session_state.messages` contains data
- Enable `DEBUG_QUERIES=true` to see what's sent to API

## Future Enhancements

Potential improvements:
- **Priority indicators**: Show which recommendations are most relevant
- **Categorization**: Group recommendations by type (comparison, deep dive, related topics)
- **Customizable count**: Let users choose how many recommendations to show
- **Recommendation history**: Track which recommendations users click most
- **Smart refresh**: Update recommendations based on entire conversation history

## Related Features

- **Chat History Context**: Automatically includes previous messages
- **Source Citations**: Shows where information comes from
- **Session Management**: Preserves conversation across app reloads

## Questions?

See also:
- `README.md` - General application documentation
- `CHAT_HISTORY_FEATURE.md` - Chat history context feature
- `DEV_SETUP.md` - Development setup guide
