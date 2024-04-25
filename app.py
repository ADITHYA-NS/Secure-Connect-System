from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from random import randint

app = Flask(__name__, static_folder='statics')

# Blom's scheme parameters
matrix_D = [[4,2,0,7,3,9,6,5,4,6],
[2,4,6,8,3,3,7,1,5,8],
[0,6,1,8,5,7,8,6,1,4],
[7,8,8,8,1,3,1,8,2,4],
[3,3,5,1,1,7,4,5,1,6],
[9,3,7,3,7,5,5,8,1,5],
[6,7,8,1,4,5,6,6,2,8],
[5,1,6,8,5,8,6,5,9,5],
[4,5,1,2,1,1,2,9,8,8],
[6,8,4,4,6,5,8,5,8,4]]  # the secret symmetric matrix
modulus = 1009

# Function to generate vanet identifier
def vanet_identifier_generator():
    return [randint(1000, 10000) for k in range(10)]

# Function to interact with the database
def insert_participant(username, identifier, private_key):
    conn = sqlite3.connect('vanet.db')
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO participants (username, identifier, private_key) VALUES (?, ?, ?)',
                       (username, json.dumps(identifier), json.dumps(private_key)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate username
        return False
    finally:
        conn.close()

def is_valid_username(username):
    # Check if the username contains spaces
    flag= username.isalnum()
    if flag==False:
        return flag


def matrix_multiplication(matrix_a, matrix_b):
    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])

    if cols_a != rows_b:
        raise ValueError("Matrices cannot be multiplied. Inner dimensions must match.")

    result = [[0] * cols_b for _ in range(rows_a)]

    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]
    #print("result:",result)

    return result

def vanet_bloms_scheme(your_privatekey, other_participant_identifier):
    # Convert identifier to matrix
    other_participant_matrix = [[i] for i in other_participant_identifier]
    shared_key = matrix_multiplication(your_privatekey,other_participant_matrix)
    #print("your_privatekey ",your_privatekey)
    #print("transpose_private_key",transpose_private_key)
    #print("other_participant_identifier",other_participant_identifier)
    #print("other_participant_matrix",other_participant_matrix)
    shared_key_new=shared_key[0][0]
    #print("Shared key",shared_key)
    #print("Shared key new",shared_key_new)
    return  shared_key_new % modulus

def get_attackers_identifiers():
    conn = sqlite3.connect('vanet.db')
    cursor = conn.cursor()
    cursor.execute('SELECT identifier FROM attack')
    result = cursor.fetchall()
    conn.close()
    attackers_identifiers = []
    for identifier in result:
        identifier_string = json.dumps(eval(identifier[0]))
        #identifier_string=identifier_string.strip("\n")
        attackers_identifiers.append(json.loads(identifier_string))
    print(attackers_identifiers)
    return attackers_identifiers

def determinant_matrix(matrix):
    if len(matrix) == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    
    determinant = 0
    for j in range(len(matrix)):
        sub_matrix = [row[:j] + row[j+1:] for row in matrix[1:]]
        sub_determinant = determinant_matrix(sub_matrix)
        if j % 2 == 0:
            determinant += matrix[0][j] * sub_determinant
        else:
            determinant -= matrix[0][j] * sub_determinant
    return determinant



def adjoint(matrix):
    def getCofactor(matrix, i, j):
        return [row[:j] + row[j + 1:] for row in (matrix[:i] + matrix[i + 1:])]

    def determinant(matrix):
        size = len(matrix)
        if size == 1:
            return matrix[0][0]
        if size == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

        det = 0
        for j in range(size):
            sign = (-1) ** j
            cofactor = getCofactor(matrix, 0, j)
            det += sign * matrix[0][j] * determinant(cofactor)

        return det
    def adjoint_cal(matrix):
        size = len(matrix)
        if size != len(matrix[0]):
            return "Matrix is not square, cannot find adjoint."
        adj = []
        for i in range(size):
            row = []
            for j in range(size):
                sign = (-1) ** (i + j)
                cofactor = getCofactor(matrix, i, j)
                minor_det = determinant(cofactor)
                row.append(sign * minor_det)
            adj.append(row)

        adj = list(map(list, zip(*adj))) 
        return adj
    adj_matrix = adjoint_cal(matrix)
    return adj_matrix
def matrix_transpose(matrix):
    transposed_matrix = []
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            if j >= len(transposed_matrix):
                transposed_matrix.append([])
            transposed_matrix[j].append(matrix[i][j])
    return transposed_matrix


#Identifier Generation
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/identifier_generator', methods=['POST'])
def identifier_generator():
    username = request.form.get('username')
    identifier = vanet_identifier_generator()

    # Convert identifier to a matrix
    identifier_matrix = [identifier]

    # Compute private key
    private_key_generated = matrix_multiplication(identifier_matrix, matrix_D)
    private_key = [[val % modulus for val in row] for row in private_key_generated]

    if is_valid_username(username)==False:
        return jsonify({'success': False, 'message': 'Invalid Username:Username can only have alphabets and numbers'})
    if len(username)>24:
        return jsonify({'success': False, 'message': 'Username should not exceed 24 characters'})
    if insert_participant(username, identifier, private_key):
        return jsonify({'success': True, 'identifier': identifier, 'private_key': private_key})
    else:
        return jsonify({'success': False, 'message': 'Username is not unique.'})
    

#connect
@app.route('/connectpage')
def connectpage():
    return render_template('connectpage.html')
@app.route('/connect', methods=['POST'])
def connect():
    your_username = request.form.get('yourUsername')
    other_username = request.form.get('otherUsername')

    # Retrieve identifiers from the database
    conn = sqlite3.connect('vanet.db')
    cursor = conn.cursor()

    cursor.execute('SELECT private_key FROM participants WHERE username=?', (your_username,))
    result = cursor.fetchone()

    if result:
        your_privatekey = json.loads(result[0])

        cursor.execute('SELECT identifier FROM participants WHERE username=?', (other_username,))
        result = cursor.fetchone()

        if result:
            other_identifier = json.loads(result[0])

            conn.close()

            shared_key = vanet_bloms_scheme(your_privatekey, other_identifier)
            return jsonify({'connectionsuccess': True, 'shared_key': shared_key})
        else:
            conn.close()
            return jsonify({'connectionsuccess': False, 'message': f'Identifier not found for user: {other_username}'})
    else:
        conn.close()
        return jsonify({'connectionsuccess': False, 'message': f'User not found: {your_username}'})
    
#Attack
@app.route('/attack')
def attack():
    return render_template('attack.html')
org_matrix=[]
@app.route('/perform_attack', methods=['POST'])
def perform_attack():
    your_username = request.form.get('yourUsername')
    identifier_matrix = get_attackers_identifiers()
    privatekey_aftermod=[]
    new_identifier_list=[]
    for identifier in identifier_matrix:
        # Convert identifier to a matrix
        #print("id",identifier)
        newid=[[i] for i in identifier]
        newid1=matrix_transpose(newid)
        #print("newid1:",newid1)
        # Compute private key
        private_key_generated = matrix_multiplication(newid1,matrix_D)
        private_key = [[val % modulus for val in row] for row in private_key_generated]
        privatekey_aftermod.append(private_key)
        new_identifier_list.append(identifier)
    #print("Identifier new:", identifier_matrix)
    #print("Identifier Matrix:", identifier_matrix)
    #print("Private Key Matrix:", privatekey_aftermod)
    transpose_new_identifier_list = [[0 for _ in range(10)] for _ in range(10)]# initializing transpose matrix of public identifiers
    transpose_new_privkeylist=transpose_new_identifier_list = [[0 for _ in range(10)] for _ in range(10)]# initializing transpose matrix of private keys
    for i in range(10): # getting the usernames of three malicious users
        #print("Identifier generated:", identifier_matrix) 
        #new_identifier_list.append([a,b,c,d,e,f,g,h,i,j])
        #print("New identifier list:",new_identifier_list)
        a,b,c,d,e,f,g,h,i,j=privatekey_aftermod #unpacking private keys
        a1=a[0]
        b1=b[0]
        c1=c[0]
        d1=d[0]
        e1=e[0]
        f1=f[0]
        g1=g[0]
        h1=h[0]
        i1=i[0]
        j1=j[0]
        new_privatekey_gen=[a1,b1,c1,d1,e1,f1,g1,h1,i1,j1]
        #new_privatekey_gen.append(a1,b1,c1,d1,e1,f1,g1,h1,i1,j1)
        #print("Priv key gen for user:",new_privatekey_gen)        
        transpose_new_identifier_list=matrix_transpose(new_identifier_list)
        transpose_new_privkeylist=matrix_transpose(new_privatekey_gen)
        #print("transpose identifier:",transpose_new_identifier_list)
        #print("Transpose of private key:",transpose_new_privkeylist)
    det = determinant_matrix(transpose_new_identifier_list)     
    #print("determinant:",det)
    adj = adjoint(transpose_new_identifier_list)
    #print("Adjoint:",adj)
    det_inv = pow(det, -1, modulus)
    inverse_matrix = [[(elem * det_inv) % modulus for elem in row] for row in adj] # calculates the inverse of public identifiers matrix
    #print("Inverese matrix:",inverse_matrix)
    org_matrix=matrix_multiplication(transpose_new_privkeylist,inverse_matrix) # matrix multiplication of private key matrix and inverse matrix
    for i in range(10):
        for j in range(10):
            org_matrix[i][j]= org_matrix[i][j] % modulus
    #print("org Matrix:")
    for row in org_matrix:
            print(row)
    #print("Attack Result:", org_matrix)
    return jsonify({'success': True, 'attack_result': org_matrix})
    
        
if __name__ == '__main__':
    app.run(debug=True)
