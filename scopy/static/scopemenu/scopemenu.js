$float_speed = 1000; //milliseconds
$float_easing = "easeOutQuint";
$menu_fade_speed = 500; //milliseconds
$closed_menu_opacity = 0.66;

$scope_menu = $("#scope_menu");
$scope_menu_menu = $("#scope_menu .menu");
$scope_menu_label = $("#scope_menu .label");
 
$(window).load(function() {
    menuPosition=$('#scope_menu').position().top;
    FloatMenu();
    $scope_menu.hover(
        function() { //mouse over
            $scope_menu_label.fadeTo($menu_fade_speed, 1);
            $scope_menu_menu.fadeIn($menu_fade_speed);
        },
        function() { //mouse out
            $scope_menu_label.fadeTo($menu_fade_speed, $closed_menu_opacity);
            $scope_menu_menu.fadeOut($menu_fade_speed);
        }
    );
});
 
$(window).scroll(function () {
    FloatMenu();
});
 
function FloatMenu() {
    var scrollAmount = $(document).scrollTop();
    var newPosition = menuPosition+scrollAmount;
    if ($(window).height() < $scope_menu.height() + $scope_menu_menu.height()) {
        $scope_menu.css("top", menuPosition);
    } else {
        $scope_menu.stop().animate({top: newPosition}, $float_speed, $float_easing);
    }
}