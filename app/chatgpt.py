from openai import OpenAI

def get_ai_response(final_sentences):
    c = "".join([final_sentences[i][0].join(final_sentences[i][1]) for i in range(len(final_sentences))])
    prompt = "the information provided may give context on how the user interprets the text, your job is to pay careful attention to this and aid, advise the user on the highlighted contents shared here: "+c

    # Function to call the LLM API and get a response
    client = OpenAI(api_key="insert-key-here")
    role="respond as an extremely knowledgable legal advisor in the south african business context"
    response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": role + " " + prompt}
                    ]
                )
    chat=response.choices[0].message.content
    response_text = chat  # Replace with actual API response logic
    if response_text:
        return response_text
    else:
        return -1