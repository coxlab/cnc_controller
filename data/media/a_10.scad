rotate([90,-90,0]){
union(){
	// silicon
	polyhedron(points=[[0,0,0],[10.01,-0.25,0],[10.01,0.25,0],[10.01,0.25,-0.05],[10.01,-0.25,-0.05]],triangles=[[1,0,2],[3,0,4],[0,1,4],[2,0,3],[2,3,1],[4,1,3]]);
	
	// pcb (shaft)
	translate([10,-2.25,0]){
		difference(){
			cube(size=[50,4.5,1]); // pcb (shaft)
			difference(){
				translate([-1.4,4.5-1.4,-1]) cube(size=[2.8,2.8,3]);
				translate([1.4,4.5-1.4,-2]) cylinder(h=5,r=1.4,$fn=100);
			}
			difference(){
				translate([-1.4,-1.4,-1]) cube(size=[2.8,2.8,3]);
				translate([1.4,1.4,-2]) cylinder(h=5,r=1.4,$fn=100);
			}
		}
	}
	
	// pcb (near samtec)
	translate([43,-4.15,0]) cube(size=[17,8.3,1]);
	
	// samtec
	translate([43,-4.15,1]) cube(size=[15.2,8.3,5.5]);
}
};