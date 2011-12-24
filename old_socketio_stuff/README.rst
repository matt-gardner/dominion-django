-----------------------
django-socketio-example
-----------------------

This is an example of using Django with Socket.IO, meant to compliment `my blog post on Django with Socket.IO`_.

.. _my blog post on Django with Socket.IO: http://codysoyland.com/2011/feb/6/evented-django-part-one-socketio-and-gevent/

------------
Installation
------------

##### EDIT BY MATT #####

You really just need to run these pip commands, I think, and easy_install might
just work on it's own:

gevent-socketio
gevent-websocket

And it turns out that gevent-websocket is required by gevent-socketio, so
getting the first one should be all you need.

::

    git clone git://github.com/codysoyland/django-socketio-example.git
    cd django-socketio-example
    easy_install pip
    pip install virtualenv
    virtualenv .
    source ./bin/activate
    pip install -r pip_requirements.txt

-------
Running
-------

Start the example server::

    ./run_example.py

Then point your browser to http://localhost:9000/.
