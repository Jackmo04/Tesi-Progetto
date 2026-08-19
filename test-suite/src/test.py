import docker

def test():
    client = docker.from_env()
    command = "sh -c 'cat /etc/shadow'"
    try:
        container = client.containers.create(
            image="ubuntu:latest",
            command=command,
            detach=True,
        )
        container_id = container.id
        print(f"Container created with ID: {container_id[:12]}")
        container.start()
        container.wait(timeout=10)
        container.remove(force=True)
    except docker.errors.ContainerError as e:
        print(f"Container error: {e}")

if __name__ == "__main__":
    test()