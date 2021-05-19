import relationship
import pandas as pd
import os


#
# def insertion(chain, in_chain, new_t):
#     location = int(find_position(in_chain, new_t, 0, len(in_chain)-1, insert=True))
#     if location == -1:
#         return []
#     else:
#         new_t = new_t.replace(".in", "")
#         chain.insert(location, new_t)
#         # print("inserted at ", location, chain)
#         return chain



def insertion(chain, in_chain, new_t):
    top = []       #theories that entail theory
    bottom = []    #theories entailed by new theory

    insert = True               #flag for insertion in existing chain
    location = len(in_chain)    #default location at end of list

    for i, t in enumerate(in_chain):
        rel = relationship.main(new_t, t, True)

        if rel == "entails_t1_t2":
            bottom.append(chain[i])

        elif "equivalent" in rel:
            #theory already exists in the chain
            if new_t == t:
                return True
            #there is an equivalent theory
            else:
                bottom.append(chain[i])

        elif rel == "entails_t2_t1":
            top.append(chain[i])
            #insertion location
            location = i

        #if there is no entailment for any theory, do not insert and create a new chain
        else:
            insert = False

    new_t = new_t.replace(".in", "")
    if insert:
        #new theory can be inserted to this chain
        chain.insert(location, new_t)
        return True
    else:
        #form new chain with select theories
        if bottom or top:
            new_chain = bottom + [new_t] + top
            return new_chain
        #no entailment for any theories in the chain
        else:
            return False



def check_duplicate_chain(new_chain, chains_list):
    # check if the existing decomposition already contains this chain
    # do not add new chain if it is a subset of any existing chain
    # if it is an extension of a newly created chain, add and delete the old one

    # the order in which theories appear should not change, so just check if all of
    # the theories in the new chain are contained in any existing chain

    #index of theory being checked in new chain
    i=0

    for j, chain in enumerate(chains_list):
        #check if new chain theories is subset of existing chain
        if len(new_chain) <= len(chain):
            for t in chain:
                if t == new_chain[i]:
                    i+=1
                    if i == len(new_chain):
                        return True
        #check if new chain is an extension of an existing chain
        else:
            if chain == new_chain[:len(chain)]:
                #remove the existing chain
                chains_list.pop(j)

    return False




def find_position(chain, new_t, low, high, insert=False):
    if low == high:
        compare_low = relationship.main(new_t, chain[low], insert)
        if compare_low == "entails_t1_t2":
            return low + 1
        elif compare_low == "entails_t2_t1":
            return low
        else:
            return -1

    if low > high:
        return low

    mid = (low+high)//2
    compare_mid = relationship.main(new_t, chain[mid], insert)

    # middle value
    if "equivalent" in compare_mid:
        # theory already exists in the chain. only the names are checked (not the contents/axioms)
        if new_t == chain[mid]:
            return -1
        # found an equivalent theory
        else:
            if insert:
                return mid
            else:
                return chain[mid]
     # lower half
    elif compare_mid == "entails_t2_t1":
        return find_position(chain, new_t, low, mid-1)
     # upper half
    elif compare_mid == "entails_t1_t2":
        return find_position(chain, new_t, mid+1, high)
     # does not belong
    else:
        return -1



def search(in_chain, new_t):
    location = find_position(in_chain, new_t, 0, len(in_chain)-1)
    if not isinstance(location, int):
        print("an equivalent theory is ", location)
    else:
        print("no equivalent theory found")


def main(csv_file, new_t, function):
    # open existing chain decomposition file, converted to DataFrame then lists
    chains_df = pd.read_csv(csv_file)
    chains_list = []
    [chains_list.append(row) for row in chains_df]
    chains_list = chains_df.values.tolist()

    for i, c in enumerate(chains_list):
        chains_list[i] = list(filter(lambda a: pd.notna(a), c))

    #add ".in" suffix to theories in chains to match input file names to check relationships
    input_chains = [[str(s) + ".in" for s in c] for c in chains_list]

    inserted = False

    # first check if new theory is consistent
    with open(new_t, "r") as f:
        lines = f.readlines()
    lines = relationship.concatenate_axioms(lines)
    relationship.replace_symbol(lines, ".\n", "")
    relationship.replace_symbol(lines, "\t", "")
    check_consistent = relationship.consistency(lines, [])


    if check_consistent is not True:
        print("your theory is inconsistent")
    else:
        # update each existing chain
        # will not need to do insertions for new chains created that already contain added theory
        num_chains_start = len(chains_list)




        for i, chain in enumerate(chains_list[:num_chains_start]):
            #condition = relationship.main(new_t, chain[0] + ".in")
            # skip the chain if inconsistent
            #if "inconsistent" in condition:
                #continue
            #else:
            if function == 1:   #insertion
                #regular insertion
                insertion_results = insertion(chain, input_chains[i], new_t)
                #print(insertion_results)

                #new chain was created
                if isinstance(insertion_results, list):
                    new_chain = insertion_results
                    #print(new_chain)


                    #check for duplicate chains
                    duplicate_found = check_duplicate_chain(new_chain, chains_list)
                    #no duplicate found, add the new chain
                    if duplicate_found is False:
                        print("new chain added", new_chain)
                        chains_list.append(new_chain)

                        new_chain = [str(c) + ".in" for c in new_chain]
                        input_chains.append(new_chain)

                        inserted = True

                #theory was inserted into the chain
                elif insertion_results:
                    inserted = True




                #try starting a new chain with select theories contained in chain
                # else:
                #     new_chain = start_new_chain(chain, input_chains[i], new_t)
                #     if new_chain and (new_chain not in chains_list):
                #         print("new chain")
                #         chains_list.append(new_chain)
                #         print(new_chain)
                #
                #         new_chain = [str(c) + ".in" for c in new_chain]
                #         input_chains.append(new_chain)
                #         inserted = True
                #some_t = new_t.replace(".in", "")
                #if some_t in new_chain:
                 #   inserted = True
                #print(inserted)

            elif function == 2: #search for an equivalent theory
                print(search(input_chains[i], new_t))

            # new theory has not been inserted anywhere. create a new chain???????
        if inserted is False:
            new_t = new_t.replace(".in", "")
            chains_list.append([new_t])
            input_chains.append([new_t + ".in"])


        print("here is the final list \n", chains_list)

        new_df = pd.DataFrame(chains_list)
        new_df.to_csv(csv_file, mode="w", index=False)
        print("chain decomposition is now updated")




def complete_insertion(csv_file):
    for file_name in os.listdir():
        if file_name.endswith(".in"):
            print(file_name)
            main(csv_file, file_name, 1)


# 1 for insert, 2 for search
main("semilinear-orderings.csv", "up_branch.in", 1)
#complete_insertion("between.csv")
