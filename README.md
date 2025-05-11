# Inventory Managment System

## Business Flow
### 🔐 Authentication
All clients first authenticate via Authentication Service.
They receive a JWT token, which is sent with all future requests.
The Facade Service validates the JWT.

### 📦 New Order Flow
Client sends request to Facade Service to create a new phone order.
Facade Service sends POST /orders to New Order Service.
New Order Service sends POST /inventory/reserve with part list.

📝Inventory Service:

If all parts available → reserves them.
If parts missing → sends POST /parts-orders to Parts Order Service to create orders for missing items.

### 🛠 Repair Flow
Client sends request to Facade Service to admit phone for repair.
Facade Service sends POST /repairs to Repair Service.
Repair Service sends POST /inventory/reserve with required parts.

📝Inventory Service:

If all parts available → reserves them.
If parts missing → sends POST /parts-orders to Parts Order Service to create orders for missing items.

### Additional features
📜Client can get the list of all orders, repairs, inventory items
📊Data is stored in Hazelcast maps
⚙️Configuration is done using Consul
![Client](https://github.com/user-attachments/assets/9ab35d08-3a97-467a-9314-82c9282914ce)


