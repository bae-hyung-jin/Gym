using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.EventSystems; // [추가] UI 위 클릭 여부 확인용
using UnityEngine.UI;           // [추가] 시점 고정 ON/OFF 버튼 글자 표시용

[RequireComponent(typeof(CharacterController))]
public class FPSController : MonoBehaviour
{
    public Transform cameraTransform;   // 플레이어 자식 카메라
    public float moveSpeed = 5f;
    public float sprintSpeed = 9f;      // Shift 키 누를 때 달리기/대시 속도
    public float jumpHeight = 1.2f;
    public float gravity = -20f;
    public float mouseSensitivity = 0.1f;

    // 1인칭 카메라 앞을 가리는 부위. 화면에서는 숨기고 그림자만 남긴다.
    // 머리는 Ch38_Body에 붙어 있어 따로 숨길 수 없다.
    public string[] hiddenInFirstPerson = { "CapDome", "CapBrim", "Hair", "Eyelashes" };

    [Header("시점 고정(마우스 잠금) 버튼 연결")]
    [SerializeField] GameObject mouseLockBtn; // [추가] ChatCanvas 안의 Btn_MouseLock
    [SerializeField] Text mouseLockLabel;     // [추가] 버튼 안의 상태 글자

    CharacterController controller;
    Animator animator;
    float pitch;
    float verticalVelocity;
    bool cursorLocked; // [추가] 현재 마우스 잠금(시점 고정) ON/OFF 상태

    void Start()
    {
        controller = GetComponent<CharacterController>();

        // [수정] 시작 시 기본은 마우스 자유 모드(OFF)
        SetMouseLock(false);

        animator = GetComponentInChildren<Animator>();
        HideFirstPersonParts();
    }

    // [추가] 유니티 버튼(Btn_MouseLock)의 On Click()에 연결해 마우스 잠금 ON/OFF 전환
    public void ToggleMouseLock() => SetMouseLock(!cursorLocked);

    // [추가] 기구 운동 진입 시 시점 고정 버튼을 즉시 숨기고 마우스 잠금을 해제
    public void SetExerciseUiHidden(bool hidden)
    {
        if (hidden && cursorLocked) SetMouseLock(false);
        if (mouseLockBtn != null) mouseLockBtn.SetActive(!hidden);
    }

    void SetMouseLock(bool locked)
    {
        cursorLocked = locked;
        Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !locked;
        if (mouseLockLabel != null)
            mouseLockLabel.text = locked ? "시점 고정: ON (ESC 해제)" : "시점 고정: OFF (클릭)";
    }

    void HideFirstPersonParts()
    {
        foreach (var r in GetComponentsInChildren<Renderer>(true))
            foreach (var part in hiddenInFirstPerson)
                if (r.name.Contains(part))
                {
                    r.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
                    break;
                }
    }


    void Update()
    {
        // [추가] 팝업·운동 중에는 시점 고정 버튼을 숨기고, 잠겨 있던 마우스도 자동 해제
        bool showLockBtn = !PlayerFreeze.Frozen && !ExerciseStation.InUse;
        if (mouseLockBtn != null && mouseLockBtn.activeSelf != showLockBtn)
            mouseLockBtn.SetActive(showLockBtn);

        var kb = Keyboard.current;
        var mouse = Mouse.current;
        if (kb == null || mouse == null) return;
        if (PlayerFreeze.Frozen)
        {
            if (cursorLocked) SetMouseLock(false);
            return;
        }

        // [추가] 시점 고정(ON) 중 ESC 키를 누르면 즉시 마우스 자유(OFF)로 복귀
        if (cursorLocked && kb.escapeKey.wasPressedThisFrame)
            SetMouseLock(false);

        // [수정] 시점 고정 ON이면 바로 회전, OFF이면 UI 위가 아닐 때 마우스 드래그로 회전
        bool overUI = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
        if (cursorLocked || (!overUI && (mouse.leftButton.isPressed || mouse.rightButton.isPressed)))
        {
            Vector2 look = mouse.delta.ReadValue() * mouseSensitivity;
            transform.Rotate(0f, look.x, 0f);
            pitch = Mathf.Clamp(pitch - look.y, -89f, 89f);
            cameraTransform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        }

        // WASD 이동 + Shift 대시
        float x = (kb.dKey.isPressed ? 1 : 0) - (kb.aKey.isPressed ? 1 : 0);
        float z = (kb.wKey.isPressed ? 1 : 0) - (kb.sKey.isPressed ? 1 : 0);
        bool isSprinting = kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
        float currentSpeed = isSprinting ? sprintSpeed : moveSpeed;
        Vector3 move = (transform.right * x + transform.forward * z).normalized * currentSpeed;

        // 점프 + 중력
        if (controller.isGrounded && verticalVelocity < 0f) verticalVelocity = -2f;
        if (controller.isGrounded && kb.spaceKey.wasPressedThisFrame)
            verticalVelocity = Mathf.Sqrt(jumpHeight * -2f * gravity);
        verticalVelocity += gravity * Time.deltaTime;
        move.y = verticalVelocity;

        controller.Move(move * Time.deltaTime);

        // [수정] 걷기·점프 캐릭터 애니메이션 복구
        if (animator != null)
        {
            float speed = new Vector3(move.x, 0f, move.z).magnitude;
            animator.SetFloat("Speed", speed);
            animator.SetFloat("MotionSpeed", 1f);
            animator.SetBool("Grounded", controller.isGrounded);
            animator.SetBool("Jump", !controller.isGrounded && verticalVelocity > 0f);
            animator.SetBool("FreeFall", !controller.isGrounded && verticalVelocity <= 0f);
        }
    }
}