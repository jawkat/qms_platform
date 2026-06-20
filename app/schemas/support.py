from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.ticket import Ticket, MessageTicket

class MessageTicketSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MessageTicket
        load_instance = True
        include_fk = True

class TicketSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Ticket
        load_instance = True
        include_fk = True
    
    nb_messages = fields.Int(dump_only=True)
    messages = fields.Nested(MessageTicketSchema, many=True, dump_only=True)
