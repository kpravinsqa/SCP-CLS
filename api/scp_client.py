from playwright.sync_api import APIRequestContext


class ScpClient:
    def __init__(self, ctx: APIRequestContext):
        self.ctx = ctx

    def forecast(self, level="PLC"):
        return self.ctx.get("/api/forecast", params={"level": level})

    def edit_plc(self, product, location, customer, month, qty):
        return self.ctx.put("/api/forecast/plc", data={"product": product, "location": location,
                                                       "customer": customer, "month": month, "qty": qty})

    def export(self, level="PLC"):
        return self.ctx.get("/api/forecast/export", params={"level": level})

    def items(self):
        return self.ctx.get("/api/items")

    def update_item(self, product, **values):
        return self.ctx.put(f"/api/items/{product}", data=values)

    def ask(self, question):
        return self.ctx.post("/api/bot/ask", data={"question": question})
