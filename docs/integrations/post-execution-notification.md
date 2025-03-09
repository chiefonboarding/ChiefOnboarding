# Post execute notification
Defined as `post_execute_notification`. Gives you the ability to send a text message or email to someone after this integration has been completed.

`type`

Either `email`, or `text`. Depends if you want to send an email or text message.

`to`

Use a fixed email or (preferably) a placeholder like `{{ manager_email }}`.

`subject`

In case of an email, define the subject header.

`message`

The message that should be send (plain text).

