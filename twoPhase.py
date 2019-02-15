# -*- coding: utf-8 -*-
"""
Created on Sat Jul 21 21:15:10 2018

@author: anshulTalati
"""

lockTable = {} 
transactionTable= {} 
waitTransactionid = []
waitTransactionList = []
timestamp = 1

def printTransactionTable():
    print("Transaction Table:")
    print("id \t Status \t Timestamp \t Items Locked")
    for i in transactionTable:
        print(i + "\t" + transactionTable[i]["status"].center(10)+ "\t" \
        + str(transactionTable[i]["timestamp"]).center(10)+ "\t" \
        + str(transactionTable[i]["itemLocking"])+ "\t")
    print("-----------------------------------------------------------")

def printLockTable():
    print("\nLock Table :")
    print("DataItem \t Lock Status \t Locking Taransaction \t ")
    for i in lockTable:
        print(i.center(8) + "\t" + str(lockTable[i]["lockStatus"]).center(12) +"\t" \
        + str(lockTable[i]["lockingTransaction"]).center(20) +"\t")
    print()

def beginTrans(command):
    global timestamp
    print("Operation: ", command)
    transId = command[1]
    transactionTable[transId] = {}
    transactionTable[transId]["status"] = "active"
    transactionTable[transId]["timestamp"] = timestamp
    transactionTable[transId]["itemLocking"] = []
    timestamp += 1
    printTransactionTable()    
    
def readData(command):
    print("Operation: ", command)
    transId = command[1]
    
    if(transactionTable[transId]["status"] != "aborted"):
        itemName = command[command.find("(") + 1:command.find(")")]
        if(itemName not in lockTable):
            lockTable[itemName] = {}
            lockTable[itemName]["lockStatus"] = "RL"
            if "lockingTransaction" in lockTable[itemName]:
                lockTable[itemName]["lockingTransaction"].append(transId)
            else:
                lockTable[itemName]["lockingTransaction"] = [transId]
            transactionTable[transId]["itemLocking"].append(itemName + ",RL")
            print("T" + transId + " has a read lock on item " + itemName)
        else:
            if(itemName in lockTable):
                if(lockTable[itemName]["lockStatus"] == "RL" and lockTable[itemName]["lockingTransaction"]):
                    lockTable[itemName]["lockingTransaction"].append(transId)
                    transactionTable[transId]["itemLocking"].append(itemName + ",RL")
                    print("T" + transId + " has a read lock on item " + itemName)
                elif(lockTable[itemName]["lockStatus"] == "WL"):
                    print("Item " + itemName + " is Writelocked and not available!")
                    checkDeadlock(transId, itemName, 'r')
                else:
                    lockTable[itemName]["lockStatus"] = "RL"
                    if "lockingTransaction" in lockTable[itemName]:
                        lockTable[itemName]["lockingTransaction"].append(transId)
                    else:
                        lockTable[itemName]["lockingTransaction"] = [transId]
                    transactionTable[transId]["itemLocking"].append(itemName + ",RL")
                    print("T" + transId + " has a read lock on item " + itemName)
    else:
        print("Operation r" + transId + " could not be performed as transaction " + transId + " is already aborted!")
                 
    printLockTable()
    printTransactionTable()
    
def unlockTransactions(transId):
    global waitTransactionList
    if(transactionTable[transId]["itemLocking"]):
        lockedItemList = transactionTable[transId]["itemLocking"].copy()
        if(lockedItemList):
            for eachLockedItem in lockedItemList:
                if(lockTable[eachLockedItem[0]]["lockStatus"] == "RL" and lockTable[eachLockedItem[0]]["lockingTransaction"]):
                    if(transId in lockTable[eachLockedItem[0]]["lockingTransaction"]):
                        lockTable[eachLockedItem[0]]["lockingTransaction"].remove(transId)
                elif(lockTable[eachLockedItem[0]]["lockStatus"] == "WL" and lockTable[eachLockedItem[0]]["lockingTransaction"]):
                    #remove item from lock table since write lock is getting removed
                    if(transId in lockTable[eachLockedItem[0]]["lockingTransaction"] and len(lockTable[eachLockedItem[0]]["lockingTransaction"]) > 1):
                        lockTable[eachLockedItem[0]]["lockingTransaction"].clear()
                        lockTable[eachLockedItem[0]]["lockStatus"] = ""
                    else:
                        lockTable[eachLockedItem[0]]["lockingTransaction"].clear()
                        lockTable[eachLockedItem[0]]["lockStatus"] = ""
                waitingTransaction = None
                index = -1
                if(waitTransactionList):
                    for eachWaitTransaction in waitTransactionList:
                       if(eachWaitTransaction[0] != "e" and eachWaitTransaction[2] == eachLockedItem[0]):
                           waitingTransaction = eachWaitTransaction
                           index += 1
                           break
                    if(waitingTransaction != None or index != -1):
                       readWaitListId = waitingTransaction[1]
                       itemName = waitingTransaction[2]
                       writeLockedId = 0
                       if (lockTable[eachLockedItem[0]]["lockStatus"] == "WL"):
                           writeLockedId = int(lockTable[eachLockedItem[0]]["lockingTransaction"][0])
                       else:
                           readLockedIds = lockTable[eachLockedItem[0]]["lockingTransaction"]
                       if(waitingTransaction[0] == "w"):
                            if(readLockedIds):
                                if(len(readLockedIds) == 1 and readWaitListId in readLockedIds and itemName == eachLockedItem[0]):
                                    updateReadToWrite(readWaitListId, itemName)
                                else:
                                    print("Transaction " + waitingTransaction[:2] + " keeps waiting in the wait list")
                            if((not(readLockedIds) or not(writeLockedId)) and itemName == eachLockedItem[0]):
                                print("Processing the operation w" + readWaitListId + " from the wait list.")
                                writeLockedId = readLockedIds[0]
                                lockTable[eachLockedItem[0]]["lockStatus"] = "WL"
                                lockTable[eachLockedItem[0]]["lockingTransaction"] = [writeLockedId]
                                del waitTransactionList[index]
                                transactionTable[writeLockedId]["itemLocking"].append(eachLockedItem[0] + ",WL")
                                print("Assigning lock to operation w" + str(writeLockedId) + " from waiting list on item " + itemName)
                                for waitTransaction in waitTransactionList:
                                    if(waitTransaction[0] == "e" and waitTransaction[1] == writeLockedId):
                                        endTrans(writeLockedId)
                            if(readWaitListId != writeLockedId):
                                print("Transaction " + waitingTransaction[:2] + " keeps waiting in the wait list")
                       elif(waitingTransaction[0] == "r"):
                            if(not(writeLockedId) and itemName == eachLockedItem[0]):
                                readLockedIds.append(readWaitListId)
                                lockTable[eachLockedItem[0]]["lockingTransaction"] = readLockedIds.copy()
                                lockTable[eachLockedItem[0]]["lockStatus"] = "RL"
                                del waitTransactionList[index]
                                transactionTable[readWaitListId]["itemLocking"].append(eachLockedItem[0] + ",RL")
                                print("Assigning lock to operation r" + str(readWaitListId) + " from waiting list on item " + itemName)

                                for waitTransaction in waitTransactionList:
                                    if(waitTransaction[0] == "e" and waitTransaction[1] == writeLockedId):
                                        endTrans(writeLockedId)
                                flag = 0
                                for x in waitTransactionList:
                                    if(x[1] in waitTransactionid and x[1] == readWaitListId):
                                        flag +=1
                                if(flag == 0):
                                    waitTransactionid.remove(readWaitListId)
                                    transactionTable[readWaitListId]["status"] = "active"
                            else:
                                print("Transaction " + waitingTransaction[:2] + " keeps waiting in the wait list")
        else:
            lockedItemList = []
            transactionTable[transId]["itemLocking"] = lockedItemList
    
def writeData(command):
    print("Operation: ", command)
    transId = command[1]
    if(transactionTable[transId]["status"] != "aborted"):
        itemName = command[command.find("(") + 1:command.find(")")]
        if(itemName not in lockTable or (itemName in lockTable and not(lockTable[itemName]["lockingTransaction"]))):
            lockTable[itemName] = {}
            lockTable[itemName]["lockStatus"] = "WL"
            if "lockingTransaction" in lockTable[itemName]:
                lockTable[itemName]["lockingTransaction"].append(transId)
            else:
                lockTable[itemName]["lockingTransaction"] = [transId]
            transactionTable[transId]["itemLocking"].append(itemName + ",WL")
            print("T" + transId + " has a write lock on item " + itemName)
        else:
            if(itemName in lockTable):
                if(lockTable[itemName]["lockStatus"] == "WL"):
                    print("Item " + itemName + " is Writelocked and not available! Proccessing for wait and die condition")
                    checkDeadlock(transId, itemName, 'w')
                if(lockTable[itemName]["lockStatus"] == "RL" and transId in lockTable[itemName]["lockingTransaction"] and len(lockTable[itemName]["lockingTransaction"]) == 1):
                    updateReadToWrite(transId, itemName)
                else:
                    checkDeadlock(transId, itemName, 'w')
    else:
        print("Operation w" + transId + " could not be performed as transaction " + transId + " is already aborted!")
                
    printLockTable()
    printTransactionTable()
    
def endTrans(transId):
    print("Operation: e"+ transId)
    if(transactionTable[transId]["status"] != "aborted"):
        if(transId in waitTransactionid and ("e" + str(transId)) not in waitTransactionList):
            waitTransactionList.append("e" + str(transId))
            print("Other Operations for transaction " + transId + " are in waiting. So, Operation e" + transId + " has been added to waitlist and could not be committed.")
        else:
            transactionTable[transId]["status"] = "committed"
            
            print("Transaction " + transId + " has committed and released all the locks held on data items")
            unlockTransactions(transId)
            transactionTable[transId]["itemLocking"].clear()
            if ("e" + str(transId)) in waitTransactionList:
                waitTransactionList.remove("e" + str(transId))
                waitTransactionid.remove(transId)
    else:
        print("Operation e" + transId + " could not be performed as transaction " + transId + " is already aborted!")
    printLockTable()
    printTransactionTable()


def checkDeadlock(transId, itemName, operationType):
    tsRequestingTrans = int(transactionTable[transId]["timestamp"])

    if(lockTable[itemName]["lockStatus"] == "WL"):
        transIDOfLockingTrans = lockTable[itemName]["lockingTransaction"][0]
    else:
        transIDOfLockingTrans = min(lockTable[itemName]["lockingTransaction"])
    tsOfLockingTrans = transactionTable[transIDOfLockingTrans]["timestamp"]
    if(tsRequestingTrans <= tsOfLockingTrans):
        transactionTable[transId]["status"] = "blocked"
        
        if(transIDOfLockingTrans == transId and operationType == "w"):
            waitTransactionList.append(operationType + str(transId) + itemName)
            waitTransactionid.append(transId)
        elif(lockTable[itemName]["lockStatus"] == "WL" and lockTable[itemName]["lockingTransaction"][0] == transId):
            waitTransactionList.append(operationType + str(transId) + itemName)
            waitTransactionid.append(transId)
        else:
            waitTransactionList.append(operationType + str(transId) + itemName)
            waitTransactionid.append(transId)
        print(operationType + transId + " is waiting for item " + itemName)
    else:
        transactionTable[transId]["status"] = "aborted"
        print("Transaction T" + transId + " is aborted")
        unlockTransactions(transId)
        transactionTable[transId]["itemLocking"].clear()
    
def updateReadToWrite(transId, itemName):
   if(lockTable[itemName]["lockStatus"] == "RL"):
       lockTable[itemName]["lockingTransaction"].clear()
       lockTable[itemName]["lockStatus"] = "WL"
       lockTable[itemName]["lockingTransaction"].append(transId)
       for i,item in enumerate(transactionTable[transId]["itemLocking"]):
           if(transactionTable[transId]["itemLocking"][i] == (itemName + ",RL")):
               transactionTable[transId]["itemLocking"][i] = str(itemName + ",WL")
       print("T" + transId + " has upgraded to write lock from read Lock on item " + itemName)        

def main():
    with open ("input6.txt") as f:
        txt = f.readlines()
        eachLine = [t.strip().replace(";","") for t in txt]
        
        for eachCommand in eachLine:
            if(eachCommand[0] == "b"):
                beginTrans(eachCommand)
            elif(eachCommand[0] == "r"):
                readData(eachCommand)
            elif(eachCommand[0] == "w"):
                writeData(eachCommand)
            elif(eachCommand[0] == "e"):
                endTrans(eachCommand[1])
            
    
main()          
            

    
    