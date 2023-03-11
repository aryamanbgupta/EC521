from vsextension.puller import VSExtensionPuller

if __name__ == "__main__":
    puller = VSExtensionPuller()
    extensions = puller.pull("live server")

    for extension in extensions:
        print(str(extension))
