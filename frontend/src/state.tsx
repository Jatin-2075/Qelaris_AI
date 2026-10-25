import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Project } from "./types";
import { api } from "./api";

type Ctx = { theme: "dark"|"cream"; setTheme:(v:"dark"|"cream")=>void; project:Project|null; setProject:(p:Project|null)=>void; projects:Project[]; refreshProjects:()=>Promise<void>; user:{username?:string;email?:string}|null; setUser:(u:{username?:string;email?:string}|null)=>void };
const Context=createContext<Ctx|null>(null);
export function AppProvider({children}:{children:ReactNode}) {
  const [theme,setThemeState]=useState<"dark"|"cream">((localStorage.getItem("rp_theme") as "dark"|"cream")||"dark");
  const [project,setProject]=useState<Project|null>(null);
  const [projects,setProjects]=useState<Project[]>([]);
  const [user,setUser]=useState<{username?:string;email?:string}|null>(()=>{try{return JSON.parse(localStorage.getItem("rp_user")||"null")}catch{return null}});
  const setTheme=(v:"dark"|"cream")=>{localStorage.setItem("rp_theme",v);setThemeState(v)};
  const refreshProjects=async()=>{const list=await api.projects();setProjects(list);setProject(old=>list.find(p=>p.id===old?.id)||list[0]||null)};
  useEffect(()=>{document.documentElement.dataset.theme=theme},[theme]);
  const value=useMemo(()=>({theme,setTheme,project,setProject,projects,refreshProjects,user,setUser}),[theme,project,projects,user]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useApp(){const value=useContext(Context);if(!value)throw new Error("useApp must be inside AppProvider");return value;}
