I am thinking:


create the concept of a message thread, which is independent of the type.

Then every thread could have a types like:
 - general - standard chat that gives corrections and responds
 - explain - chat that was started with some context and has special explanation identity
 - 

Allow explain threads to be created from explain threads?
 could be but then don't make them linked 


What would be the home screen then? I want to be able to:
 - start a chat
 - see my last chats
 - start a practice session
 - start a vocab session
 - start a conjugation session
 - translate something
 - manage my data 

So if there were one of those navbars along the bottom of the screen with options for:
 - Data & setttings
 - Practice & Explanation
   -> Leads to overview of Practice sessions and previous explanation threads
   -> Allows starting new Practice session or ask about something
 - Vocab & Conjugation
   -> Leads to overview of Vocab & Conjugation history/stats
 - Chat
 - Translate
   - Translation interface and past translations

Then in the top right/left quick buttons for starting a chat or going to profile or something, depending on the screen.

Important:
 - all explanations and translations are saved
 -> These play an important role in practice sessions and vocab/conjugation

The user flow would be:
 - Start on chat page
   - see overview of previous chats, can continue or start new one
   - in chat, the bottom navbar disappears and it's just chat focused with a Home button in the top left
   - in chat, you can start explain thread
   - in explain, you can start explain thread. 
     (If explain thread was started from a chat even if you are multiple explain threads into it, there will be a button to go back to the chat that you came from)
   - at any point you can translate something
 - user goes to practice & explanation
   - can see list tabbed list of previous activity, one for sessions one for explanation
   - from any explanation thread, you can start a practice session
   -> This should be all about understanding
 - user goes to vocab & conjugation
   - also sees history of vocab & conjugation exercises and can start new one
   - lots of open questions here not sure how to separate these or if mixed is good?
     - I think it might be good mixed.. Could get creative. Wouldn't just have to be flashcards.
     - Completing sentences for instance.
   -> This should be all about expanding vocabulary
 - Data & settings
   - delete history items/change defaults etc To be decided
   - could also just be a general profile thing
 - Translate
   - See previous translations
   - make new one
     - over time possibly allow images, voice
   - make this return super useful detailed info with all stuff like gender, regionality, example usage, etc



Many thoughts:

I think when user sends a message, AI should respond in a structure like this (although it will be adjusted depending on thread type):
{
  "assistant_response": "Natural reply to user",
  "correction": {
    "corrected": "I went to the store yesterday",
    "notes": ["Use past tense of go -> went"]
  },
}


How are explanations going to work?
 -> could be an "Explain" button for a correction
    then that would be the topic
 -> It should be possible to start an explanation thread about anything. Then it just wouldn't have a seed

What about practice sessions?
 -> Would also need some kind of a seed
 - also a more specific structure probably

What about translations?
 -> Could be a translate button for a message
 are much more flexible
 translations are really just saved but don't need any references to the chat


For each kind of thread, be it chat, explain, or practice, there could be a seed. This seed could be a conversation topic, an explanation topic and correction context, or some kind of practice target. I believe creating models like this:

Thread
 id
 user_id
 parent_thread_id (not really sure about this but could be a reference to where an explain thread started for example or maybe attach it on the message since it would come from a message?)
 title
 type (chat | explain | practice)
 seed (flexible json, depends on type)
 created_at
 updated_at

Message
 id
 thread_id
 role (user | assistant | system | developer)
 content (json that may or may not include correction and also depends on the thread type)
 metadata
 created_at
 updated_at


Translation
 from_text
 to_text
 from_languate
 to_languate

Not sure about how the translations are exactly going to be set up but I am imagining them to be more of a 'placed on top' kind of feature. They are not going to be actual threads and there will probably be some special handling depending on how they are used.

Currently, I am thinking that there are these use cases for translations:
 - translate button next to a received response
   -> would show an extra box underneath the message with the translation
 - select and translate
   -> would show some kind of overlay, where the from and to text are shown, I think
 - standard translate page

I feel like a lot of this also depends on how well I can make some kind of selecting, contextmenus, and overlays work.. So there will be relatively complex UI features involved in determining the direction of this.

Something to consider is that I will want the corrections and explanations to be integrated with suggestions for practice sessions, and the translation with vocab exercises. The actual implementation of this will come much later than the chat and explain implementation but I always want to keep that in mind.

I think these three models are a good starting ground to get started on the first chat, explain, and translate features, though, and should be extensible enough to figure out other features as I figure out more about how the interface is going to work.

What do you think about all of this?



EDGE CASES
 - what about corrections that cover multiple things?
 