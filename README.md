How to Run code
--------------

First make sure to install mininet. Follow prior lab instructions to do so.  

Then, open the program "X2Go Client" and perform the following steps:
- [ ] set the host to `bolt.cs.ucr.edu'
- [ ] set the login to your netID
- [ ] set the session type to XFCE

Click ok and then log into your session.  

From here, a new window will open up with a gui to your bolt desktop.
Open a terminal and ssh into the appropirate machiene like so:
(Don't forget to include -X so we can use graphics)  

```bash
ssh -X acast050@wch129-33.cs.ucr.edu
```

From here use the command
```bash
virtualbox &
```

To open up virtual box and get the mininet vm running
Back in the terminal window, ssh into mininet like so:

```bash
ssh -X -p 2222 mininet@localhost
```

Once you are inside mininet, use the command
```bash
sudo mn --custom topo.py --topo myfirsttopo
```

Then use the command
```bash
xterm b1 b2 b3 b4
```

This will open four individual windows representing the four nodes we will be using
From each of the nodes we call `python bridge.py` to run the program.
