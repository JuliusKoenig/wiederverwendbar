from nicegui import app, ui

@ui.page('/multicast_receiver')
def multicast_receiver():
    ui.label('This page will show messages from the index page.')

def send(message: str):
    for client in app.clients('/multicast_receiver'):
        with client:
            ui.notify(message)

@ui.page('/')
def page():
    ui.button('Send message', on_click=lambda: send('Hi!'))
    ui.link('Open receiver', '/multicast_receiver', new_tab=True)

ui.run()