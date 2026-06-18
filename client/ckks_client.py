from config import *
from service import *

def main():
    public_key, secret_key = load_or_create_keys()
    eval_mult_key, eval_sum_key = generate_eval_keys(secret_key)

    setup_response = setup_eval_keys(USER_ID, KEY_ID, eval_mult_key, eval_sum_key)
    
    print("setup response:", setup_response.status_code)
    # num of polynomials = 2
    # Ring Dimension = 16384
    # num of modulus towers = d+2 = 3 why? flexableautoext때문
    # bytes per modulus prime = 8 
    
    while True:
        
        mode = input("r: 등록\nv: 단일 인증 \na: Plaintext와 CKKS 전체 비교\nd: Genuine/Impostor 분포 실험\nq: 종료\n\n입력 : ")

        if mode.lower() == "r":
            register_user(public_key)

        elif mode.lower() == "v":
            verify_one(public_key, secret_key)

        elif mode.lower() == "a":
            run_verify_experiment(public_key, secret_key)
            
        elif mode.lower() == "d":
            run_distribution_experiment()

        elif mode.lower() == "q":
            break

        else:
            print("Invalid input. Please enter r, v, a, d, m or q.")


if __name__ == "__main__":
    main()