import consul

def main():
    # Connect to local Consul agent
    c = consul.Consul(host='localhost', port=8500)

    # Define key-values to set in Consul
    kvs = {
        "cluster-name": "dev",
        "queue-name": "order-processing-queue",
        "repairs-map": "repairs-map",
        "inventory-map": "inventory-map",
        "order-map": "order-map",
        "order-parts-map": "order-parts-map",
        "auth-map":"auth-users-map",
    }

    for key, value in kvs.items():
        print(f"Setting {key} = {value}")
        c.kv.put(key, value)

    print("All keys written to Consul.")

if __name__ == "__main__":
    main()