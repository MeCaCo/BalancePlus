from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate, Goal as GoalSchema
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=GoalSchema)
def create_goal(
        goal_data: GoalCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    goal = Goal(**goal_data.dict(), user_id=current_user.id)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/", response_model=List[GoalSchema])
def get_goals(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    goals = db.query(Goal).filter(Goal.user_id == current_user.id).offset(skip).limit(limit).all()
    return goals


@router.get("/{goal_id}", response_model=GoalSchema)
def get_goal(
        goal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.put("/{goal_id}", response_model=GoalSchema)
def update_goal(
        goal_id: int,
        goal_data: GoalUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    for key, value in goal_data.dict(exclude_unset=True).items():
        setattr(goal, key, value)

    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
        goal_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return None