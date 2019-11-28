import json
from datetime import datetime

from decimal import Decimal
from psycopg2.extras import RealDictCursor

from healthcheckbot.common.model import WatcherModule, ParameterDef
import psycopg2


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(DecimalEncoder, self).default(o)


class DatabaseQueryWatcher(WatcherModule):
    PARAMS = [
        ParameterDef('db_connection', is_required=True),
        ParameterDef('queries', is_required=True),
    ]

    def __init__(self, application):
        super().__init__(application)
        self.db_connection = {}
        self.queries = {}

    def serialize_state(self, state: object) -> [dict, None]:
        return json.dumps(state, cls=DecimalEncoder)

    def on_configured(self):
        self.conn = psycopg2.connect(**self.db_connection, cursor_factory=RealDictCursor)

    def obtain_state(self, trigger) -> object:
        cur = self.conn.cursor()
        try:
            result = {}
            for name, query in self.queries.items():
                result[name] = []
                cur.execute(query)
                result[name] = [dict(x) for x in cur.fetchall()]
            return result
        finally:
            cur.close()