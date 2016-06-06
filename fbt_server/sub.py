import os

def recursive_replace(root, pattern, replace):
    for dir, subdirs, names in os.walk(root):
        for name in names:
            path = os.path.join(dir, name)
            try:
                text = open(path).read()
                if pattern in text:
                     open(path, 'w').write(text.replace(pattern, replace))
            except IOError as e:
                print "pass file: %s because error: %s" % (path,e)

if __name__ == "__main__":
    recursive_replace(".","pipeline(transaction=False)", "pipeline(transaction=False)")
    print "Process Ok"
