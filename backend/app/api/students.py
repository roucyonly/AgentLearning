"""
学生相关 API
班级绑定、获取班级信息
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import User, Class, StudentClassMapping
from app.models.schemas import StudentJoinClass, StudentClassResponse
from app.core.tracing import tracing_logger
from app.api.auth import get_current_user

router = APIRouter()


@router.post("/join", response_model=StudentClassResponse)
async def join_class(
    join_data: StudentJoinClass,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    学生加入班级

    - **invite_code**: 班级邀请码
    """
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生才能加入班级"
        )

    tracing_logger.info(f"Student {current_user.id} attempting to join class with code: {join_data.invite_code}")

    # 查找班级
    target_class = db.query(Class).filter(
        Class.invite_code == join_data.invite_code
    ).first()

    if not target_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无效的邀请码"
        )

    # 检查是否已加入
    existing = db.query(StudentClassMapping).filter(
        StudentClassMapping.student_id == current_user.id,
        StudentClassMapping.class_id == target_class.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已加入该班级"
        )

    # 加入班级
    new_mapping = StudentClassMapping(
        student_id=current_user.id,
        class_id=target_class.id
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    tracing_logger.info(f"Student {current_user.id} joined class {target_class.id}")

    # 获取教师信息
    teacher = db.query(User).filter(User.id == target_class.teacher_id).first()

    return StudentClassResponse(
        id=new_mapping.id,
        student_id=current_user.id,
        class_id=target_class.id,
        class_name=target_class.class_name,
        teacher_name=teacher.username if teacher else "Unknown"
    )


@router.get("/classes", response_model=list[StudentClassResponse])
async def get_student_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生已加入的所有班级"""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生才能查看已加入的班级"
        )

    mappings = db.query(StudentClassMapping).filter(
        StudentClassMapping.student_id == current_user.id
    ).all()

    result = []
    for mapping in mappings:
        target_class = db.query(Class).filter(Class.id == mapping.class_id).first()
        if target_class:
            teacher = db.query(User).filter(User.id == target_class.teacher_id).first()
            result.append(
                StudentClassResponse(
                    id=mapping.id,
                    student_id=mapping.student_id,
                    class_id=mapping.class_id,
                    class_name=target_class.class_name,
                    teacher_name=teacher.username if teacher else "Unknown"
                )
            )

    return result


@router.get("/classes/{class_id}", response_model=StudentClassResponse)
async def get_class_detail(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取班级详细信息"""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生才能查看班级详情"
        )

    mapping = db.query(StudentClassMapping).filter(
        StudentClassMapping.student_id == current_user.id,
        StudentClassMapping.class_id == class_id
    ).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该班级"
        )

    target_class = db.query(Class).filter(Class.id == class_id).first()
    teacher = db.query(User).filter(User.id == target_class.teacher_id).first()

    return StudentClassResponse(
        id=mapping.id,
        student_id=mapping.student_id,
        class_id=mapping.class_id,
        class_name=target_class.class_name,
        teacher_name=teacher.username if teacher else "Unknown"
    )
