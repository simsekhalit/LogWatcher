
var simple_chart_config = {
	chart: {
		container: "#rules",
		scrollbar: "fancy"
	},
	
	nodeStructure: {
		text: { value: "AND" },
		children: [
			{
				text: { name: "('WHOLE', 'EQ', '123456', False, True)" },
			},
			{
				text: { name: "('WHOLE', 'EQ', 'ABCDEF', False, True)" }
			}
		]
	}
};

// // // // // // // // // // // // // // // // // // // // // // // // 

// var config = {
// 	container: "#OrganiseChart-simple"
// };

// var parent_node = {
// 	text: { name: "Parent node" }
// };

// var first_child = {
// 	parent: parent_node,
// 	text: { name: "First child" }
// };

// var second_child = {
// 	parent: parent_node,
// 	text: { name: "Second child" }
// };

// var simple_chart_config = [
// 	config, parent_node,
// 		first_child, second_child 
// ];
