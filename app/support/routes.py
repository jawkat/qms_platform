from flask import render_template
from flask_login import login_required
from app.support import support


@support.route('/')
@support.route('/mes-tickets')
@login_required
def mes_tickets():
    return render_template('support/tickets.html')
