You probably have seen bots which allow you to send them token of your bot and then handle updates providing some functionality for your bot.
<br>
This type of bots are called <b>multibots</b>. They are created using webhooks.
<br>

This is the example of simple multibot.<br>
In order to reproduce this example you need to have <b>domain and ssl connection</b>.
<br>
If you have, go to config.py and specify your data.
<br>
There is also file called <b>nginx_conf.conf</b>,  we will use nginx as proxy-server and this file is example nginx.conf file.
<br>
Make sure that server_name and port are the same in both config and nginx_conf
<br>
(nginx_conf.conf IS NOT complete, you would probably use tools like certbot to add ssl connection to it)
<br>
Also, in this example I used dictionary as tokens storage, but in production you should use database so that you can re-set webhooks in case bot restarts.