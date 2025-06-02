from ollama import chat

MODEL = 'llama3.2:1b'

system_message = 'You are a helpful assistant that responds what your asked if you have knowledge of it. I you are not sure about something just say you do not know'
conversation_history = [
    {
        'role':'system',
        'content':system_message
    },
]

def chat_with_history(user_input):
    conversation_history.append({
        'role':'user',
        'content':user_input
    })

    full_reply = ''
    # Generate response
    stream = chat(
        model=MODEL, 
        messages=conversation_history,
        stream=True
    )

    for chunk in stream:
        part = chunk['message']['content']
        print(part, end='', flush=True)
        full_reply += part

    conversation_history.append({
        'role':'assistant',
        'content':full_reply
    })

def main():
    print("Send 'exit' to quit at any time")
    while True:
        user_input = input()
        if user_input == 'exit':
            break
        chat_with_history(user_input)
        print('')


if __name__ == "__main__":
    main()
